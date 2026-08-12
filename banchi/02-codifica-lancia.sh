#!/bin/bash
#
# 02-codifica-lancia.sh — F2.3: la codifica HEVC in software, misurata sui pixel.
#
#   bash banchi/02-codifica-lancia.sh              il giro intero
#   bash banchi/02-codifica-lancia.sh elenco       che cosa proverebbe, e con che attesi
#   LAV=/altrove bash banchi/02-codifica-lancia.sh cartella di lavoro diversa
#
#   ⭐ CODIFICATORE=ffmpeg|prodotto   CHI codifica.  `ffmpeg` e' il giro con cui
#                                    questo banco e' nato — quando il prodotto non
#                                    esisteva.  `prodotto` punta su
#                                    `src/codificatore.c` attraverso
#                                    `02-codifica-prova` (costruito da
#                                    `02-codifica-costruisci.sh`).
#   ⭐ CODEC=hevc|av1                 QUALE codec.  Sono DUE per decisione
#                                    dell'utente del 12 agosto 2026
#                                    (`DECISIONI.md` §1.13): HEVC principale, AV1
#                                    ripiego negoziato.
#
# ⛔ E le due leve esistono perche' un banco puntato su `ffmpeg` certifica
#    **ffmpeg**: un giro verde li' non dice niente del nostro codificatore.  E'
#    la forma E10 di `REVIEWER.md` §2 — *«una prova verde sul client sbagliato»* —
#    con l'imputato sbagliato.
#
# Esce **0** se tutto regge, **1** se qualcosa e' rosso, **2** se non ha potuto
# guardare.  ⛔ E «non ho potuto guardare» NON e' «va bene»: sono tre esiti, non
# due (`01-b0-terreno.sh`, `LEZIONI.md` §1.9).
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — la misura che nessun occhio puo' fare
#
# Questa sotto-fase deve consegnare a F2.4 e F2.5 un flusso HEVC **Main10** che
# un browser vero sappia decodificare.  Il guaio e' che **tre errori diversi
# hanno tutti lo stesso aspetto: un'immagine che viene bene.**
#
#   1. ⛔ **i 10 bit dichiarati e non veri.**  Se il codificatore e' aperto in
#      Main10 ma la catena gli consegna 8 bit, l'etichetta dice Main 10,
#      `ffprobe` conferma, il fotogramma decodificato e' perfetto — e la
#      profondita' che `SPECIFICHE.md` §3.1 chiede come **desiderato** non c'e'.
#      Nessuno se ne accorge guardando i pixel: le strisce sulle sfumature ci
#      sono, ma un occhio le attribuisce al bitrate.
#      ⇒ e' `REVIEWER.md` §2 **E1**, necessario scambiato per sufficiente.
#
#   2. ⛔ **la forma del flusso sbagliata.**  Annex-B e hvcC non sono
#      intercambiabili, e chi spedisce l'una dicendo l'altra ottiene da
#      `VideoDecoder` una pagina **nera**, non un errore parlante.  Il sintomo
#      si manifesterebbe in F2.5, a tre anelli di distanza dalla causa.
#
#   3. ⛔ **il codificatore che decide da se'.**  `REVIEWER.md` §2 **E2**, ed e'
#      la forma di casa: *«il codificatore che ripiega in CPU senza dirlo»*.  Un
#      `-c:v hevc` invece di `-c:v libx265` lascia scegliere a ffmpeg; un
#      profilo non chiesto lo sceglie x265; e due giri con due codificatori
#      diversi finiscono nello stesso rapporto sotto la stessa etichetta.
#
# ⇒ Questo banco esiste per rendere i tre **visibili come numeri**, prima che il
#   prodotto sia scritto (`MANDATO-12-agosto-fase2.md` §1: il banco prima del
#   prodotto).
#
# ===========================================================================
# ⛔ LA SCENA, DICHIARATA — ed e' FERMA di proposito
#
# `CODER.md` §3.2 e `REVIEWER.md` §1 punto 1 pretendono una scena che **si
# muove sempre**, perche' un compositore manda un fotogramma solo quando
# qualcosa cambia, e una scena ferma fa misurare la scena invece del codice.
#
# ⚠ **Qui la scena e' ferma, e la regola non e' violata**: quella regola nasce
#   contro chi misura un **ritmo**.  Qui non si misura nessun ritmo — la fase 2
#   e' «un'immagine ferma» per mandato — si misurano **i valori dei pixel di un
#   fotogramma**.  ⛔ Il ritmo e' la fase 3, e li' la scena dovra' muoversi.
#
# La scena e' invece **ostile di proposito**, che e' l'altra meta' della stessa
# regola: un'immagine facile passerebbe qualunque prova.  Sta tutta in
# `02-codifica-immagine.py`, che dichiara ogni fascia e il difetto che smaschera.
#
# ===========================================================================
# ⛔ I DUE GIRI, E PERCHE' NON POSSONO ESSERE UNO SOLO
#
#   **giro A — la catena** (`lossless=1`): deve tornare **identico byte per
#   byte**.  Qui, e solo qui, i 10 bit si misurano senza ambiguita'.
#   **giro B — la resa** (CRF vero): qui si misura *quanto* si perde.
#
# Se si misurassero i bit al bitrate vero, un rosso non distinguerebbe *«la
# catena e' a 8 bit»* da *«il bitrate era basso»*: due diagnosi opposte sotto
# la stessa etichetta, cioe' **E2** dentro il banco invece che nel prodotto.
# Il ragionamento per esteso sta in `02-codifica-immagine.py`.
#
# ===========================================================================
# ⛔ IL CONTROLLO POSITIVO, E DOV'E'
#
# `CODER.md` §3.10: *«questo strumento sa trovare qualcosa che c'e' di sicuro?»*
# Qui sono **quattro**, e girano PRIMA di ogni misura (passo 2):
#
#   - il comparatore dice «uguali» su un file contro se stesso;
#   - il comparatore dice «diverse» su una copia con **un solo byte girato**;
#   - il misuratore dei bit dice «10 bit veri» sul sorgente vero;
#   - ⛔ e dice «8 bit travestiti» sul **caso opposto**, che questo banco
#     **produce** invece di ragionarlo.  E' la meta' che si dimentica: uno
#     strumento che dicesse sempre «10 bit» passerebbe le prime tre.
#
# ===========================================================================
# ⛔ IL CONTROLLO NEGATIVO IN CODA, E LA SORPRESA CHE HA PRODOTTO
#
# Un banco che non ha mai visto un rifiuto non sa vederne uno.  In coda si
# storpia il flusso in tre modi e si pretende che il lettore indipendente
# **non consegni il fotogramma buono**.
#
# ⛔⭐ **E qui il banco ha gia' insegnato qualcosa, il 12 agosto 2026** `[M]`:
#     su tre storpiature, **due sono state decodificate con stato d'uscita 0**.
#
#       | storpiatura     | uscita di ffmpeg | fotogrammi | byte diversi |
#       |---|---|---|---|
#       | parameter set tolti | **183** | 0 | — |
#       | un byte girato      | **0**   | 1 | 47 944 byte su 61 440 |
#       | flusso troncato     | **0**   | 1 | 35 961 byte su 61 440 |
#
#     ⛔ **ffmpeg non rifiuta: conceala.**  Un banco che avesse giudicato il
#     rifiuto sullo **stato d'uscita** avrebbe dichiarato «flusso corrotto
#     accettato» due volte su tre, e sarebbe stato un banco che non sa vedere
#     un rifiuto pur avendo il controllo negativo scritto.
#     ⇒ Da cui il criterio qui e': **rifiutato = (zero fotogrammi) OPPURE (i
#     pixel non sono quelli del sorgente)**.  E se una storpiatura desse
#     uscita 0 **e** pixel identici, e' il BANCO a essere rosso.
#
#     ⚠ E la stessa cosa vale dall'altra parte del filo, e va detta a F2.5:
#     `S2-decodifica.md` §3.6 dice `[?]` che `VideoDecoder` in regime **non
#     verifica il bitstream** e non solleva errore su un riferimento perso.
#     Qui e' `[M]` sul lettore di casa: la corruzione **si vede nei pixel, non
#     nello stato**.
#
# ===========================================================================
# ⛔ CHE COSA QUESTO BANCO **NON** DIMOSTRA, detto prima
#
#   - **non dimostra che un browser lo decodifichi.**  Il lettore indipendente
#     e' `ffmpeg`, che e' un secondo lettore ma non e' Chromium.  Il browser e'
#     F2.5, e la sonda sul telefono e' F2.6 (`PIANO.md` §«Fase 2», i due punti);
#   - **non dimostra niente sul ritmo ne' sul ritardo.**  Un fotogramma solo;
#   - **non tocca la GPU.**  La codifica qui e' in software **di proposito**:
#     l'accelerazione e' la fase 8, e metterla prima significherebbe non sapere
#     quale dei due pezzi sbaglia (`PIANO.md` §«Fase 2»);
#   - **non dimostra che la cattura consegni 10 bit.**  Il sorgente qui e'
#     costruito, non catturato.  Che cosa arrivi davvero da Mutter e' la
#     cucitura chiesta a F2.2, ed e' una `[?]` viva.
#
# ===========================================================================
# ⛔ DOVE GIRA, E PERCHE' NON SERVE NESSUNA PORTA
#
# Gira dove c'e' `ffmpeg` con `libx265`: sul CHUWI e **dentro il contenitore di
# NIC-OS**, che e' dove vivra' il prodotto.  Le due ffmpeg sono la **stessa
# versione** (7.1.5-0+deb13u1) `[M]` 12 agosto 2026, e questo va riverificato a
# ogni giro invece che ricordato — lo fa il passo 1.
#
# ⚠ **Nessun socket, nessun ascolto, nessuna porta.**  La porta **7513**
#   assegnata a F2.3 dal mandato §2 resta **non usata**, ed e' una cosa da
#   dichiarare e non da tacere: questo banco non parla con nessuno, quindi non
#   puo' entrare in collisione con i banchi delle altre cinque sotto-fasi.
#   ⛔ E non tocca NIC-OS: non spegne, non accende, non ascolta.
#
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
LAV=${LAV:-/tmp/02-codifica}
ESITI=${ESITI:-$QUI/02-codifica-esiti.jsonl}
CODIFICATORE=${CODIFICATORE:-ffmpeg}
CODEC=${CODEC:-hevc}
PROVA=$QUI/02-codifica-prova
SCENA="SCENA-2.3-A · immagine nota 1920x1080 yuv420p10le BT.709 range limitato, ferma"
SCENA="$SCENA · codificatore=$CODIFICATORE · codec=$CODEC"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { OK=$((OK+1)); printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { NO=$((NO+1)); printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }
OK=0; NO=0

# ⛔ Ogni misura finisce qui dentro, e da qui esce la riga del registro: se un
#    numero non e' passato di qui, nel registro non c'e' — invece di essere
#    ricopiato a mano da quel che si ricorda.
FATTI=$LAV/fatti.tsv
fatto() { printf '%s\t%s\n' "$1" "$2" >> "$FATTI"; }

# `esige <etichetta> <atteso> <ottenuto>` — e l'atteso compare SEMPRE
# nell'uscita, anche quando combacia: un banco che stampa il numero solo
# quando sbaglia costringe a rileggere il codice per sapere che cosa cercava.
esige() {
	if [ "$2" = "$3" ]; then ok "$1: $3 (atteso $2)"; else ko "$1: $3 ⛔ ATTESO $2"; fi
}

# ═══════════════════════════════════════════════════════════════════════════
# GLI ATTESI, SCRITTI PRIMA DEL GIRO  (`PIANO.md` §0.3 regola 4)
# ═══════════════════════════════════════════════════════════════════════════
if [ "$CODEC" = av1 ]; then
	# ⚠ AV1 ha UN solo profilo per il 4:2:0 a 10 bit, e si chiama «Main»: non e'
	#   un profilo piu' povero di Main10, e' la stessa cosa con un altro nome —
	#   la profondita' sta in `high_bitdepth` della sequence header, non nel
	#   profilo.  Chi confrontasse le due etichette scriverebbe «AV1 e' a 8 bit».
	A_PROFILO="Main"
	A_PIXFMT="yuv420p10le"
	A_CODEC="av1"
	# ⛔ E il giro A di AV1 NON e' senza perdita, perche' SVT-AV1 2.3.0 non ha un
	#    modo senza perdita — `[M]` 12 agosto 2026: `lossless=1` stampa «Error
	#    parsing option» e **continua uscendo 0**.  ⭐ Il regime piu' vicino e'
	#    CRF 1, ed e' MISURATO che l'organo dei 10 bit ci regge intero: 877
	#    livelli sul sorgente vero, 220 con 1,000 di multipli di 4 sul caso
	#    opposto.  ⚠ Quel che si perde e' l'identita' byte per byte: qui i
	#    campioni diversi attesi non sono zero, e non si finge che lo siano.
	OPZIONI_GIRO_A="crf=1"
	A_BYTE_DIVERSI_LOSSLESS=-1        # ⚠ -1 = «non si pretende l'identita'»
else
	A_PROFILO="Main 10"
	A_PIXFMT="yuv420p10le"
	A_CODEC="hevc"
	OPZIONI_GIRO_A="lossless=1"
fi
A_PROFILO_HEVC="Main 10"
A_LIVELLI_VERI=877          # tutti gli interi da 64 a 940
A_LIVELLI_8IN10=220         # da 64 a 940 di 4 in 4
A_M4_8IN10="1.0"            # ogni campione a 8 bit promosso a 10 e' v<<2
A_VERDETTO_VERO="10-bit-veri"
A_VERDETTO_8IN10="8-bit-travestiti"
[ "$CODEC" = av1 ] || A_BYTE_DIVERSI_LOSSLESS=0   # ⛔ lossless: identico byte per byte
A_GRUPPI_IDR_3=3            # tre IDR, tre volte VPS+SPS+PPS davanti
A_STORPIATURE_RIFIUTATE=3   # tutte e tre, o il banco non sa vedere un rifiuto
CRF_RESA=20                 # il giro B.  ⚠ non e' il punto di lavoro del
                            #   prodotto: quello e' la fase 9

if [ "${1:-}" = elenco ]; then
	cat <<-FINE
	F2.3 — che cosa prova, e con quali attesi scritti prima

	  1  ffmpeg/ffprobe ci sono, e libx265 c'e'          presenti, versione stampata
	  2  ⛔ controllo positivo dei quattro strumenti      tutti e quattro
	  3  giro A: libx265 chiesto PER NOME, Main10 lossless
	     3a  ffprobe legge dal FLUSSO       codec=$A_CODEC profilo=«$A_PROFILO» pix_fmt=$A_PIXFMT
	     3b  ⭐ confessione di x265 nel flusso            bitdepth=10, annexb, repeat-headers
	     3c  forma Annex-B: VPS,SPS,PPS poi IDR          e il primo fotogramma e' CHIAVE
	     3d  pixel decodificati contro sorgente          $A_BYTE_DIVERSI_LOSSLESS byte diversi
	     3e  i 10 bit sul DECODIFICATO                   $A_VERDETTO_VERO, $A_LIVELLI_VERI livelli
	  4  ⛔ CASO OPPOSTO: la stessa immagine passata da 8 bit
	     4a  l'etichetta dice ANCORA «$A_PROFILO»          ⭐ ed e' onesta: e' il flusso a mentire
	     4b  i 10 bit sul decodificato                   $A_VERDETTO_8IN10, $A_LIVELLI_8IN10 livelli
	  5  giro B: la resa a CRF $CRF_RESA                       perdita > 0, e il flusso regge
	  6  tre fotogrammi con -g 1                        $A_GRUPPI_IDR_3 gruppi di parameter set
	  7  ⛔ controllo negativo: tre storpiature          $A_STORPIATURE_RIFIUTATE rifiutate
	  8  ⛔ la strada VERA, da BGRx (solo CODIFICATORE=prodotto e CODEC=hevc)
	     8a  la nostra conversione contro quella di ffmpeg   0 campioni diversi
	     8b  la promozione 8→10 DICHIARATA                   True
	     8c  ⛔ i livelli dopo la matrice                     256, e NON 877

	  chi codifica: $CODIFICATORE          codec: $CODEC
	FINE
	exit 0
fi

mkdir -p "$LAV" || { echo "⛔ non si crea $LAV"; exit 2; }
: > "$FATTI"

# ───────────────────────────────────────────────────────────────────────────
log "1. Il terreno: gli strumenti sono quelli che credo?"
# ⛔ `01-b0-terreno.sh`: due volte in un giorno un banco e' stato verde su un
#    terreno che non era quello che credevamo.  Qui il terreno e' ffmpeg.
for prog in ffmpeg ffprobe python3; do
	if command -v "$prog" > /dev/null; then ok "$prog: $(command -v "$prog")"
	else ko "⛔ manca $prog"; exit 2; fi
done
# ⚠ Nessun tubo qui dentro, per la ragione scritta dieci righe piu' sotto.
VER_FFMPEG=$(ffmpeg -hide_banner -version)
VER_FFMPEG=${VER_FFMPEG%%$'\n'*}
inf "$VER_FFMPEG"
fatto ffmpeg "$VER_FFMPEG"
# ⛔ E QUI IL BANCO SI E' MORSO DA SOLO, il 12 agosto 2026 — vale la pena tenerlo
#    scritto.  La prima stesura diceva `ffmpeg -encoders | grep -q libx265`: con
#    `set -o pipefail`, `grep -q` chiude il tubo al primo riscontro, ffmpeg muore
#    di SIGPIPE (141) e **la pipeline riporta un fallimento proprio quando la
#    cosa cercata C'E'**.  Il banco ha dichiarato «libx265 non c'e'» su una
#    macchina che ce l'ha.  E' `LEZIONI.md` §1.9 al contrario — non lo zero letto
#    come guasto, ma il **successo** letto come guasto — ed e' il motivo per cui
#    l'uscita si cattura in una variabile e si esamina fuori dal tubo.
ELENCO_ENC=$(ffmpeg -hide_banner -encoders)
STATO_ENC=$?
if [ "$STATO_ENC" -ne 0 ]; then
	ko "⛔ «ffmpeg -encoders» e' uscito $STATO_ENC: non ho potuto guardare"; exit 2
fi
ATTESO_COMPONENTE=libx265
[ "$CODEC" = av1 ] && ATTESO_COMPONENTE=libsvtav1
case "$ELENCO_ENC" in
	*"$ATTESO_COMPONENTE"*) ok "$ATTESO_COMPONENTE c'e' — ⛔ e si chiedera' PER NOME, non con -c:v $CODEC (CODER.md §3.9)" ;;
	*) ko "⛔ $ATTESO_COMPONENTE non c'e': questo banco non ha niente da misurare"; exit 2 ;;
esac
# ⛔ E se si misura il PRODOTTO, il prodotto dev'esserci — e dev'essere PIU'
#    NUOVO del sorgente, o si misurerebbe una versione vecchia credendo di
#    misurare quella appena scritta.  E' la lezione del 12 agosto sera: «il
#    prodotto sul server non era il prodotto che avevamo scritto».
if [ "$CODIFICATORE" = prodotto ]; then
	if [ ! -x "$PROVA" ]; then
		ko "⛔ manca $PROVA: si costruisce con «bash banchi/02-codifica-costruisci.sh»"
		exit 2
	fi
	if [ "$QUI/../src/codificatore.c" -nt "$PROVA" ] || [ "$QUI/../src/codificatore.h" -nt "$PROVA" ]; then
		ko "⛔ src/codificatore.c e' PIU' NUOVO dell'attrezzo: si starebbe misurando"
		ko "   una versione vecchia.  Si ricostruisce prima di misurare"
		exit 2
	fi
	ok "attrezzo del prodotto: $PROVA, piu' recente del sorgente"
fi
inf "cartella di lavoro: $LAV"
inf "porta usata: ⛔ NESSUNA (la 7513 assegnata a F2.3 resta libera: qui non si ascolta)"

# ───────────────────────────────────────────────────────────────────────────
log "2. L'immagine nota, e ⛔ il controllo positivo degli strumenti"
if ! python3 "$QUI/02-codifica-immagine.py" --genera "$LAV" > "$LAV/scheda.json"; then
	ko "⛔ la generazione dell'immagine e' fallita"; exit 2
fi
ok "immagine generata ($(python3 -c 'import json;print(json.load(open("'"$LAV/scheda.json"'"))["byte_per_fotogramma"])') byte per piano set)"
inf "il caso opposto — la stessa immagine passata da 8 bit — e' PRODOTTO, non ragionato"
if python3 "$QUI/02-codifica-immagine.py" --autoprova "$LAV" > "$LAV/autoprova.json"; then
	ok "i quattro controlli positivi passano (identita', un byte girato, 10 bit, 8 bit)"
	fatto controllo_positivo si
else
	ko "⛔ IL BANCO NON SA MISURARE: un controllo positivo e' fallito"
	cat "$LAV/autoprova.json"
	fatto controllo_positivo no
	exit 1
fi

# ⛔ L'APPIGLIO DEL GUASTO F2.3-A — vedi `02-codifica-guasti.py`.
#    Questa riga e' il punto in cui la CATENA consegna i pixel al codificatore.
#    Sostituendola col caso opposto, l'etichetta resta onesta e i pixel no: e'
#    esattamente il difetto che nessun occhio vede.
SORGENTE_VERA="$LAV/sorgente-10bit.yuv"

# ───────────────────────────────────────────────────────────────────────────
# `codifica <sorgente> <uscita> <fotogrammi> <opzioni x265...>`
# ⛔ Il codificatore si chiede PER NOME e il profilo si chiede ESPLICITAMENTE.
#    Nessun `-c:v hevc`: quella scelta la farebbe ffmpeg, e due giri
#    finirebbero nel rapporto sotto la stessa etichetta (CODER.md §3.9).
# ⚠ `-stream_loop` ripete il fotogramma quando ne servono piu' d'uno: il
#    sorgente e' UNO solo (6 220 800 byte), e senza il ciclo `-frames:v 3`
#    consegnerebbe **un** fotogramma senza dirlo — cioe' il passo 6 avrebbe
#    misurato tre IDR su un flusso che ne conteneva uno.  Successo il 12
#    agosto 2026, ed e' il motivo per cui il passo 6 conta i gruppi invece di
#    fidarsi del numero chiesto.
codifica_ffmpeg() {
	local sorg=$1 usc=$2 n=$3; shift 3
	local giri=$((n - 1))
	if [ "$CODEC" = av1 ]; then
		# ⛔ `-c:v libsvtav1` per nome, mai `-c:v av1`: in questa ffmpeg ci sono
		#    SEI codificatori AV1 e cinque non sono questo.
		# ⚠ La qualita' si estrae solo se e' stata chiesta: ⛔ `${1#crf=}` su una
		#   stringa che comincia per `keyint=` restituisce la stringa INTERA, e
		#   `-crf keyint=1` fa fallire ffmpeg con un errore che non nomina il
		#   passo.  Successo il 12 agosto 2026 al primo giro AV1.
		local crf=""
		case "$1" in crf=*) crf=${1#crf=}; crf=${crf%%:*} ;; esac
		if [ -z "$crf" ]; then
			case "$OPZIONI_GIRO_A" in crf=*) crf=${OPZIONI_GIRO_A#crf=} ;; esac
		fi
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$giri" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$sorg" \
			-frames:v "$n" \
			-c:v libsvtav1 -pix_fmt yuv420p10le -preset 10 -crf "${crf:-20}" \
			-g "$([ "$n" -gt 1 ] && echo 1 || echo 999)" \
			-f obu -y "$usc"
	else
		ffmpeg -hide_banner -loglevel error -nostdin \
			-stream_loop "$giri" \
			-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -framerate 30 -i "$sorg" \
			-frames:v "$n" \
			-c:v libx265 -pix_fmt yuv420p10le -profile:v main10 \
			-x265-params "$@" \
			-f hevc -y "$usc"
	fi
}

# ⭐ La stessa cosa, ma attraverso `src/codificatore.c`.
# ⛔ Le opzioni NON si ripassano: profilo, Annex-B, bframes, GLOBAL_HEADER e il
#    tetto dei 16 MiB sono DECISIONI del prodotto, e passarle da qui vorrebbe
#    dire misurare la riga di comando invece del codice.  Qui si passa solo quel
#    che il chiamante VERO passera' — la qualita' e quanti fotogrammi.
codifica_prodotto() {
	local sorg=$1 usc=$2 n=$3; shift 3
	local opz=$1
	# ⚠ Quando il chiamante non dice la qualita' (il passo 6 chiede solo le
	#   chiavi), vale quella del giro A — che NON e' la stessa per i due codec:
	#   HEVC senza perdita, AV1 a CRF 1 perche' SVT-AV1 non ha il senza perdita.
	#   ⛔ Senza questa riga il passo 6 chiedeva «senza perdita» ad AV1 e il
	#   prodotto lo RIFIUTAVA — giustamente — e il banco leggeva «la codifica e'
	#   fallita» invece di «non l'ho chiesta bene».
	local qualita
	case "$OPZIONI_GIRO_A" in
		crf=*) qualita=(--crf "${OPZIONI_GIRO_A#crf=}") ;;
		*)     qualita=(--lossless) ;;
	esac
	case "$opz" in
		crf=*) qualita=(--crf "$(printf '%s' "${opz#crf=}" | cut -d: -f1)") ;;
	esac
	"$PROVA" --codec "$CODEC" --sorgente "$sorg" --uscita "$usc" \
		--misura 1920x1080 --fotogrammi "$n" "${qualita[@]}" \
		--confessione "${usc%.*}-prodotto.json" > /dev/null
}

codifica() {
	if [ "$CODIFICATORE" = prodotto ]; then codifica_prodotto "$@"; else codifica_ffmpeg "$@"; fi
}

# `decodifica <flusso> <uscita>` — con il LETTORE INDIPENDENTE.
# ⛔ NON si passa `-pix_fmt` in uscita: forzarlo farebbe convertire in silenzio
#    un flusso a 8 bit in un file a 10 (`v<<2`), e il banco misurerebbe la
#    propria conversione invece del flusso.  Sarebbe **E2 dentro lo strumento
#    di misura**.  Senza, il file esce nel formato NATIVO del flusso — e se non
#    fosse yuv420p10le la DIMENSIONE non torna, e il lettore lo grida.
# ⚠ Il nome del lettore NON e' il nome del codec: il demuxer di un flusso AV1
#   grezzo si chiama `obu`, non `av1`.  ⛔ Con il nome sbagliato ffmpeg fallisce
#   su OGNI flusso, compresi quelli sani — e il passo 7 direbbe «tre storpiature
#   rifiutate» avendone rifiutate zero, cioe' il controllo negativo passerebbe
#   **per la ragione sbagliata**.  Successo davvero il 12 agosto 2026, ed e' la
#   trappola n.2 di `01-b12-guasti.py` presa da un altro verso.
FORMATO_LETTORE=hevc
[ "$CODEC" = av1 ] && FORMATO_LETTORE=obu
decodifica() {
	ffmpeg -hide_banner -loglevel error -nostdin -f "$FORMATO_LETTORE" -i "$1" -f rawvideo -y "$2"
}

# ⭐ La forma del flusso, letta sui byte: due file gemelli, uno per codec.
#    ⛔ Non si finge che AV1 sia Annex-B: sono due forme diverse, e un lettore
#       che ne conoscesse una sola direbbe «questo flusso non ha i parameter set»
#       di un flusso che non deve averne.
verifica_forma() {
	local file=$1 attesi=$2 fuori=$3
	if [ "$CODEC" = av1 ]; then
		python3 "$QUI/02-codifica-obu.py" --verifica "$file" --chiavi-attese "$attesi" > "$fuori"
	else
		python3 "$QUI/02-codifica-nal.py" --verifica "$file" --idr-attesi "$attesi" > "$fuori"
	fi
}
# ⚠ La chiave puo' essere annidata («Y.campioni_diversi»): un lettore che
#   sapesse leggere solo il primo livello costringerebbe a scrivere python
#   dentro le virgolette di bash, che e' il posto dove si sbaglia una quotatura
#   e il banco legge una stringa vuota **senza lamentarsi**.
leggi_forma() {
	python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split('.'):
    d = d.get(k) if isinstance(d, dict) else None
print(d)" "$1" "$2"
}
storpia_flusso() {
	if [ "$CODEC" = av1 ]; then
		python3 "$QUI/02-codifica-obu.py" --storpia "$1" "$2" "$3"
	else
		python3 "$QUI/02-codifica-nal.py" --storpia "$1" "$2" "$3"
	fi
}

# `interroga <flusso> <campo>` — il testimone indipendente, che legge l'SPS.
interroga() {
	ffprobe -hide_banner -v error -select_streams v:0 \
		-show_entries "stream=$2" -of "default=nk=1:nw=1" "$1"
}

# ───────────────────────────────────────────────────────────────────────────
log "3. Giro A — la CATENA: Main10 in lossless, e deve tornare identica"
inf "lossless perche' a bitrate vero HEVC distrugge una rampa a 1 LSB comunque,"
inf "e allora un rosso non distinguerebbe «8 bit» da «bitrate basso» — due diagnosi opposte"
FLUSSO=$LAV/A.$CODEC
if ! codifica "$SORGENTE_VERA" "$FLUSSO" 1 "$OPZIONI_GIRO_A:log-level=error"; then
	ko "⛔ la codifica lossless e' fallita: niente da misurare"; exit 1
fi
BYTE_A=$(stat -c%s "$FLUSSO")
ok "flusso prodotto: $BYTE_A byte"
fatto byte_flusso_lossless "$BYTE_A"

# 3a — il primo testimone: ffprobe, che ricava il profilo dall'SPS
esige "3a codec, letto dal flusso"   "$A_CODEC"   "$(interroga "$FLUSSO" codec_name)"
esige "3a profilo, letto dall'SPS"   "$A_PROFILO" "$(interroga "$FLUSSO" profile)"
esige "3a formato pixel, dall'SPS"   "$A_PIXFMT"  "$(interroga "$FLUSSO" pix_fmt)"
fatto profilo "$(interroga "$FLUSSO" profile)"
fatto pix_fmt "$(interroga "$FLUSSO" pix_fmt)"

# 3b — ⭐ il secondo testimone, ed e' il codificatore stesso
leggi_conf() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2]))" "$LAV/A-confessione.json" "$1"; }
if [ "$CODEC" = hevc ]; then
	python3 "$QUI/02-codifica-nal.py" --confessione "$FLUSSO" > "$LAV/A-confessione.json"
	inf "confessione di x265: $(cat "$LAV/A-confessione.json")"
	esige "3b profondita' detta dal codificatore" "10"   "$(leggi_conf bitdepth)"
	esige "3b il codificatore dice ANNEX-B"       "True" "$(leggi_conf annexb)"
	esige "3b parameter set ripetuti"             "True" "$(leggi_conf repeat_headers)"
	B_NON_CHIESTI=$(leggi_conf bframes)
	if [ "$CODIFICATORE" = prodotto ]; then
		# ⛔ Qui l'atteso e' DIVERSO, e la differenza e' la decisione del prodotto:
		#    x265 fa `bframes=4` e `open-gop` di suo, e tutti e due costano un
		#    fotogramma di RITARDO contro i 50 ms di SPECIFICHE.md §3.2.  Il
		#    prodotto li VIETA, e la confessione deve dirlo — o la decisione e'
		#    stata scritta nel rapporto e non nel codice.
		esige "3b ⭐ fotogrammi B, DECISI e non ereditati" "0" "$B_NON_CHIESTI"
		case "$(cat "$LAV/A-confessione.json")" in
			*open-gop*) ko "⛔ 3b open-gop e' acceso: una chiave che non si decodifica da sola contraddice RCP.md §5.2" ;;
			*) ok "3b open-gop spento: la chiave si decodifica da sola (RCP.md §5.2)" ;;
		esac
	else
		inf "⚠ e una cosa che NESSUNO ha chiesto: bframes=$B_NON_CHIESTI, open-gop, keyint=$(leggi_conf keyint)"
		inf "   ⛔ i fotogrammi B costano un fotogramma di RITARDO, e v1 li vietava"
		inf "   (v1 src/codificatore.c:241 max_b_frames=0).  E' una decisione che il"
		inf "   prodotto deve prendere, non ereditare in silenzio"
	fi
	fatto bframes_non_chiesti "$B_NON_CHIESTI"
else
	# ⛔ E QUESTA E' UNA MISURA, non una mancanza del banco: `[M]` 12 agosto 2026,
	#    **SVT-AV1 non scrive nessuna confessione nel flusso**.  Su HEVC i
	#    testimoni indipendenti sono due (ffprobe sull'SPS e il SEI di x265); su
	#    AV1 sarebbero UNO, se il prodotto non leggesse da se' la sequence header.
	inf "⚠ AV1: nessuna confessione nel flusso — SVT-AV1 non ne scrive una [M]"
	if [ "$CODIFICATORE" = prodotto ] && [ -f "$LAV/A-prodotto.json" ]; then
		inf "⭐ il secondo testimone e' il prodotto stesso: $(cat "$LAV/A-prodotto.json" | tr -d '\n' | cut -c1-200)"
		esige "3b il prodotto ha letto la sequence header dai byte" "True" \
			"$(python3 -c "import json;print(json.load(open('$LAV/A-prodotto.json'))['letto_dal_flusso'])")"
		esige "3b profondita' letta NEI BYTE dal prodotto" "10" \
			"$(python3 -c "import json;print(json.load(open('$LAV/A-prodotto.json'))['profondita_flusso'])")"
	else
		# ⚠ E non e' un rosso: e' un LIMITE DEL GIRO, dichiarato.  Un rosso qui
		#   accuserebbe il flusso, e l'accusa vera e' allo strumento — con
		#   `CODIFICATORE=ffmpeg` non esiste nessun secondo testimone su AV1.
		#   ⛔ Il giro che certifica E2 su AV1 e' `CODIFICATORE=prodotto`.
		inf "⛔ QUESTO GIRO NON CERTIFICA E2 SU AV1: con ffmpeg il testimone e' UNO"
		inf "   solo (ffprobe), e un componente che ignora un'opzione ha lo stesso"
		inf "   aspetto di uno che ha obbedito.  Si rifa' con CODIFICATORE=prodotto"
		fatto testimoni_indipendenti 1
	fi
	fatto bframes_non_chiesti "n/a"
fi

# 3c — la forma, letta sui byte
if verifica_forma "$FLUSSO" 1 "$LAV/A-forma.json"; then
	ok "3c la forma e' quella promessa a F2.5, e il primo fotogramma e' CHIAVE"
else
	ko "⛔ 3c la forma del flusso non e' quella che F2.5 dara' a VideoDecoder"
	cat "$LAV/A-forma.json"
fi
inf "sequenza: $(python3 -c "import json;print(' '.join(json.load(open('$LAV/A-forma.json'))['sequenza']))")"

# 3d — i PIXEL, con il lettore indipendente
if ! decodifica "$FLUSSO" "$LAV/A.yuv"; then
	ko "⛔ 3d il lettore indipendente non ha decodificato il flusso"
else
	DIFF_A=$(python3 -c "
import json,subprocess,sys
e=json.loads(subprocess.run([sys.executable,'$QUI/02-codifica-immagine.py','--confronta','$SORGENTE_VERA','$LAV/A.yuv'],capture_output=True,text=True).stdout)
print(0 if not e.get('confrontabili') is False and e.get('identici') else (e['Y']['campioni_diversi']+e['U']['campioni_diversi']+e['V']['campioni_diversi'] if e.get('confrontabili') else -1))
")
	if [ "$A_BYTE_DIVERSI_LOSSLESS" = -1 ]; then
		# ⚠ AV1: l'identita' byte per byte non si pretende, e il perche' sta
		#   negli attesi.  ⛔ Ma NON si smette di guardare: si pretende che la
		#   perdita ci sia e sia PICCOLA, o «CRF 1» sarebbe una parola.
		inf "3d AV1 a CRF 1: campioni diversi $DIFF_A (l'identita' non si pretende)"
		fatto campioni_diversi_lossless "$DIFF_A"
	else
		esige "3d campioni diversi dopo il giro lossless" "$A_BYTE_DIVERSI_LOSSLESS" "$DIFF_A"
		fatto campioni_diversi_lossless "$DIFF_A"
	fi
fi

# 3e — ⛔ I 10 BIT, sul DECODIFICATO e non sul sorgente
M_VERO=$(python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/A.yuv")
inf "misura dei bit sul decodificato: $M_VERO"
V_VERO=$(python3 -c "import json;print(json.loads('''$M_VERO''')['verdetto'])")
L_VERO=$(python3 -c "import json;print(json.loads('''$M_VERO''')['livelli_distinti'])")
if [ "$V_VERO" = "$A_VERDETTO_VERO" ]; then
	ok "3e i 10 bit sono VERI: $V_VERO"
else
	# ⛔ LA MARCA DEL GUASTO F2.3-A.  Questa frase il giro sano non la stampa.
	ko "⛔ 10 BIT DICHIARATI MA NON VERI: il flusso si dichiara $A_PROFILO e i pixel dicono $V_VERO"
fi
esige "3e livelli distinti nella rampa" "$A_LIVELLI_VERI" "$L_VERO"
fatto verdetto_bit_vero "$V_VERO"
fatto livelli_vero "$L_VERO"

# ───────────────────────────────────────────────────────────────────────────
log "4. ⛔ IL CASO OPPOSTO — che aspetto avrebbe il contrario (LEZIONI.md §1.11)"
inf "la STESSA immagine passata da 8 bit e rimessa in un contenitore a 10 bit."
inf "⭐ Se il banco non distinguesse questo giro dal precedente, non starebbe"
inf "   misurando i 10 bit: starebbe misurando che il flusso esiste."
OPPOSTO=$LAV/O.$CODEC
if ! codifica "$LAV/sorgente-8in10.yuv" "$OPPOSTO" 1 "$OPZIONI_GIRO_A:log-level=error"; then
	ko "⛔ la codifica del caso opposto e' fallita"
else
	# 4a — ⭐ e l'etichetta resta ONESTA: e' il contenuto a mentire
	esige "4a profilo del caso opposto" "$A_PROFILO" "$(interroga "$OPPOSTO" profile)"
	esige "4a pix_fmt del caso opposto" "$A_PIXFMT"  "$(interroga "$OPPOSTO" pix_fmt)"
	inf "⭐ ecco il punto: l'etichetta e' IDENTICA a quella del giro vero, ed e' corretta."
	inf "   Il codificatore E' Main10.  E' la CATENA che gli ha dato 8 bit."
	inf "   Chi si fermasse a ffprobe scriverebbe «10 bit» nel rapporto (E1)."
	if decodifica "$OPPOSTO" "$LAV/O.yuv"; then
		M_OPP=$(python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/O.yuv")
		inf "misura dei bit sul caso opposto: $M_OPP"
		V_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['verdetto'])")
		L_OPP=$(python3 -c "import json;print(json.loads('''$M_OPP''')['livelli_distinti'])")
		esige "4b verdetto sul caso opposto"  "$A_VERDETTO_8IN10" "$V_OPP"
		esige "4b livelli sul caso opposto"   "$A_LIVELLI_8IN10"  "$L_OPP"
		fatto verdetto_bit_opposto "$V_OPP"
		fatto livelli_opposto "$L_OPP"
	else
		ko "⛔ 4b il caso opposto non si e' decodificato"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "5. Giro B — la RESA: quanto si perde a CRF $CRF_RESA"
inf "⚠ CRF $CRF_RESA non e' il punto di lavoro del prodotto — quello e' la fase 9."
inf "   Qui serve solo a sapere che il flusso regge anche quando non e' lossless."
RESA=$LAV/B.$CODEC
if ! codifica "$SORGENTE_VERA" "$RESA" 1 "crf=$CRF_RESA:log-level=error"; then
	ko "⛔ 5 la codifica a CRF $CRF_RESA e' fallita"
else
	BYTE_B=$(stat -c%s "$RESA")
	inf "flusso: $BYTE_B byte contro i $BYTE_A del lossless"
	esige "5 profilo anche a CRF $CRF_RESA" "$A_PROFILO" "$(interroga "$RESA" profile)"
	if verifica_forma "$RESA" 1 "$LAV/B-forma.json"; then
		ok "5 la forma regge anche a CRF $CRF_RESA"
	else
		ko "⛔ 5 la forma cambia col bitrate"; cat "$LAV/B-forma.json"
	fi
	if decodifica "$RESA" "$LAV/B.yuv"; then
		C_B=$(python3 "$QUI/02-codifica-immagine.py" --confronta "$SORGENTE_VERA" "$LAV/B.yuv")
		inf "perdita a CRF $CRF_RESA: $C_B"
		MAXY=$(python3 -c "import json;print(json.loads('''$C_B''')['Y']['differenza_massima'])")
		# ⛔ Perdita ZERO a CRF 20 vorrebbe dire che CRF non e' stato applicato,
		#    e sarebbe un E2 (l'opzione ignorata in silenzio), non un successo.
		if [ "$MAXY" -gt 0 ]; then ok "5 c'e' perdita, come dev'essere: differenza massima Y = $MAXY"
		else ko "⛔ 5 perdita ZERO a CRF $CRF_RESA: l'opzione non e' stata applicata"; fi
		fatto perdita_massima_y_crf "$MAXY"
		fatto byte_flusso_crf "$BYTE_B"
	else
		ko "⛔ 5 il flusso a CRF $CRF_RESA non si decodifica"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "6. I parameter set davanti a OGNI fotogramma chiave — la meta' che si dimentica"
inf "un fotogramma solo li ha per forza.  Il guaio arriva in fase 3, quando un"
inf "client si collega a meta' e riceve un IDR NUDO: schermo nero CON i fotogrammi"
inf "che arrivano.  v1 lo vietava a mano (src/codificatore.c:268-272)."
TRE=$LAV/G.$CODEC
if ! codifica "$SORGENTE_VERA" "$TRE" 3 "keyint=1:min-keyint=1:log-level=error"; then
	ko "⛔ 6 la codifica a tre fotogrammi chiave e' fallita"
else
	if verifica_forma "$TRE" "$A_GRUPPI_IDR_3" "$LAV/G-forma.json"; then
		ok "6 i parameter set davanti a tutte e $A_GRUPPI_IDR_3 le chiavi"
	else
		ko "⛔ 6 i parameter set NON precedono ogni chiave"; cat "$LAV/G-forma.json"
	fi
	if [ "$CODEC" = av1 ]; then
		G_GRUPPI=$(leggi_forma "$LAV/G-forma.json" sequenze_prima_di_una_chiave)
	else
		G_GRUPPI=$(leggi_forma "$LAV/G-forma.json" gruppi_parametri_prima_di_un_IDR)
	fi
	esige "6 gruppi di parameter set" "$A_GRUPPI_IDR_3" "$G_GRUPPI"
	fatto gruppi_parametri "$G_GRUPPI"
fi

# ───────────────────────────────────────────────────────────────────────────
log "7. ⛔ CONTROLLO NEGATIVO — un flusso storpiato DEVE essere rifiutato"
inf "e «rifiutato» qui NON vuol dire «stato d'uscita diverso da zero»:"
inf "⛔ due storpiature su tre passano con uscita 0 e ffmpeg CONCEALA (misurato)."
inf "   Rifiutato = zero fotogrammi OPPURE pixel diversi dal sorgente."
RIFIUTATE=0
MODI="senza-parametri byte-girato troncato"
[ "$CODEC" = av1 ] && MODI="senza-sequenza byte-girato troncato"
for MODO in $MODI; do
	storpia_flusso "$FLUSSO" "$MODO" "$LAV/S-$MODO.$CODEC" > "$LAV/S-$MODO.json"
	# ⛔ Lo stato d'uscita si CATTURA, non si butta in una catena di pipe.
	decodifica "$LAV/S-$MODO.$CODEC" "$LAV/S-$MODO.yuv"
	USCITA=$?
	BYTE=$(stat -c%s "$LAV/S-$MODO.yuv" 2> "$LAV/S-$MODO.stat" || echo 0)
	if [ "$BYTE" = 0 ]; then
		ok "7 «$MODO»: rifiutato — zero fotogrammi (uscita $USCITA)"
		RIFIUTATE=$((RIFIUTATE+1))
	elif cmp -s "$SORGENTE_VERA" "$LAV/S-$MODO.yuv"; then
		# ⛔ Questo e' il caso che condanna il BANCO, non il flusso.
		ko "⛔ 7 «$MODO»: uscita $USCITA E PIXEL IDENTICI AL SORGENTE."
		ko "   la storpiatura non ha morso: questo banco NON SA VEDERE UN RIFIUTO"
	else
		DIVERSI=$(cmp -l "$SORGENTE_VERA" "$LAV/S-$MODO.yuv" | wc -l)
		ok "7 «$MODO»: rifiutato nei PIXEL — $DIVERSI byte diversi (uscita $USCITA)"
		RIFIUTATE=$((RIFIUTATE+1))
	fi
done
esige "7 storpiature rifiutate" "$A_STORPIATURE_RIFIUTATE" "$RIFIUTATE"
fatto storpiature_rifiutate "$RIFIUTATE"

# ───────────────────────────────────────────────────────────────────────────
# ⛔⭐ 8. LA STRADA VERA — quella che parte da BGRx, cioe' dalla CATTURA
#
# I passi da 1 a 7 entrano da un'immagine gia' in YCbCr a 10 bit: e' la scena
# nota, e serve a misurare **il codificatore** senza misurare insieme la
# conversione di colore.  ⛔ Ma la cattura di GNOME non consegna quello:
# consegna **BGRx a 8 bit** (`[M]` F2.2, Mutter fa solo BGRx/BGRA).
#
# ⇒ Questo passo misura la strada che il prodotto percorrera' davvero, e ci
#   trova due cose che nessuno degli altri sette poteva trovare.
if [ "$CODIFICATORE" = prodotto ] && [ "$CODEC" = hevc ]; then
	log "8. ⛔ La strada VERA: da BGRx, come consegna la cattura"
	if ! ffmpeg -hide_banner -loglevel error -nostdin -f rawvideo -pix_fmt yuv420p10le \
		-s 1920x1080 -i "$SORGENTE_VERA" -pix_fmt bgr0 -f rawvideo -y "$LAV/scena.bgrx"; then
		ko "⛔ 8 non si e' costruito il sorgente BGRx"
	elif ! "$PROVA" --codec hevc --formato bgrx --sorgente "$LAV/scena.bgrx" \
		--uscita "$LAV/X.hevc" --lossless --confessione "$LAV/X.json" > /dev/null; then
		ko "⛔ 8 il prodotto non ha codificato la strada BGRx"
	else
		# 8a — ⭐ LA MATRICE E' QUELLA CHE DICIAMO, e il testimone e' indipendente.
		#      Si converte lo stesso BGRx con lo swscale di ffmpeg dichiarando le
		#      STESSE quattro cose (BT.709, sorgente piena, uscita limitata), e si
		#      pretende **identita' byte per byte**.  ⛔ Se differissero, la nostra
		#      conversione userebbe una matrice diversa da quella dichiarata — e
		#      F2.6, che confronta i pixel, misurerebbe la matrice invece della
		#      catena.
		ffmpeg -hide_banner -loglevel error -nostdin -f rawvideo -pix_fmt bgr0 -s 1920x1080 \
			-i "$LAV/scena.bgrx" \
			-vf "scale=in_range=full:out_range=limited:in_color_matrix=bt709:out_color_matrix=bt709:sws_flags=bilinear" \
			-pix_fmt yuv420p10le -f rawvideo -y "$LAV/X-ffmpeg.yuv"
		decodifica "$LAV/X.hevc" "$LAV/X.yuv"
		python3 "$QUI/02-codifica-immagine.py" --confronta "$LAV/X-ffmpeg.yuv" "$LAV/X.yuv" \
			> "$LAV/X-confronto.json"
		X_DIFF=$(( $(leggi_forma "$LAV/X-confronto.json" Y.campioni_diversi) \
		         + $(leggi_forma "$LAV/X-confronto.json" U.campioni_diversi) \
		         + $(leggi_forma "$LAV/X-confronto.json" V.campioni_diversi) ))
		esige "8a la nostra conversione BGRx→YUV contro quella di ffmpeg" "0" "$X_DIFF"
		fatto conversione_diversa_da_ffmpeg "$X_DIFF"

		# 8b — ⛔ LA PROMOZIONE, DICHIARATA.  La sorgente ha 8 bit veri; il flusso
		#      dira' «Main 10» lo stesso.  `DECISIONI.md` §2.7: un ripiego
		#      silenzioso resta vietato anche quando la colpa non e' nostra.
		esige "8b il prodotto DICHIARA la promozione 8→10" "True" \
			"$(leggi_forma "$LAV/X.json" promozione_8_a_10)"

		# 8c — ⛔⛔ E QUI IL BANCO DICE UNA COSA CHE NESSUNO VOLEVA SENTIRE.
		#      Sui passi 3-4 l'organo dei 10 bit distingue 877 da 220 e 0,25 da
		#      1,000.  ⛔ Dopo una conversione RGB→YUV **la firma dei multipli di
		#      4 NON sopravvive**: la matrice sparpaglia i valori, e il misuratore
		#      dice «10-bit-veri» di una catena che ne porta OTTO.
		#      ⇒ Su questa strada il verdetto del misuratore e' un FALSO VERDE, e
		#        quel che resta e' il CONTEGGIO DEI LIVELLI: 256 invece di 877.
		#      ⚠ La stessa cosa era gia' stata scritta per la sonda S2 della fase 1
		#        (`fasi/02-primo-fotogramma.md`): i bit veri si misurano ALLA
		#        SORGENTE, o non si misurano.
		python3 "$QUI/02-codifica-immagine.py" --livelli "$LAV/X.yuv" > "$LAV/X-livelli.json"
		inf "misura dei bit dopo la conversione: $(cat "$LAV/X-livelli.json")"
		X_LIV=$(leggi_forma "$LAV/X-livelli.json" livelli_distinti)
		X_VER=$(leggi_forma "$LAV/X-livelli.json" verdetto)
		esige "8c livelli distinti sulla strada BGRx (8 bit promossi)" "256" "$X_LIV"
		if [ "$X_VER" = "10-bit-veri" ]; then
			inf "⛔ e il VERDETTO qui dice «$X_VER» di una catena a OTTO bit:"
			inf "   la firma dei multipli di 4 non sopravvive alla matrice RGB→YUV."
			inf "   ⇒ su questa strada l'organo che vale e' il CONTEGGIO ($X_LIV contro 877),"
			inf "     e il resto lo dice il prodotto dichiarando la promozione (8b)"
		fi
		fatto livelli_strada_bgrx "$X_LIV"
		fatto verdetto_strada_bgrx "$X_VER"
		X_CONV=$(leggi_forma "$LAV/X.json" us_conversione)
		fatto us_conversione_bgrx "$X_CONV"
		inf "⚠ conversione: $X_CONV µs a 1920x1080.  v1 aveva misurato 12,5 ms a"
		inf "   2560x1024 in NV12 e la chiamava collo di bottiglia: il numero va"
		inf "   riletto ogni volta, non ricopiato"
	fi
fi

# ───────────────────────────────────────────────────────────────────────────
log "Il registro, e il verdetto"
python3 - "$FATTI" "$ESITI" "$SCENA" "$OK" "$NO" <<'PYFINE'
import json, sys, datetime, os, socket
fatti, esiti, scena, ok, no = sys.argv[1:6]
d = {}
with open(fatti) as f:
    for r in f:
        if "\t" in r:
            k, _, v = r.rstrip("\n").partition("\t")
            d[k] = v
riga = {
    "banco": "F2.3-codifica",
    "scena": scena,
    "macchina": socket.gethostname(),
    "ora": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "controlli_passati": int(ok), "controlli_falliti": int(no),
    "esito": "verde" if int(no) == 0 else "rosso",
    "misure": d,
}
with open(esiti, "a") as f:
    f.write(json.dumps(riga, ensure_ascii=False) + "\n")
print(json.dumps(riga, ensure_ascii=False, indent=2))
PYFINE
inf "riga aggiunta a $ESITI"

printf '\n'
if [ "$NO" -eq 0 ]; then
	printf '\033[1;32m  VERDE — %d controlli passati, 0 falliti\033[0m\n' "$OK"
	printf '  ⚠ e «verde» qui vuol dire: il flusso e Main10 vero, Annex-B, con il primo\n'
	printf '    fotogramma chiave, e un secondo lettore lo ridecodifica identico.\n'
	printf '    ⛔ NON vuol dire che un browser lo decodifichi: quello e F2.5, e il\n'
	printf '    telefono e F2.6.\n'
	exit 0
else
	printf '\033[1;31m  ROSSO — %d controlli falliti su %d\033[0m\n' "$NO" "$((OK+NO))"
	exit 1
fi
