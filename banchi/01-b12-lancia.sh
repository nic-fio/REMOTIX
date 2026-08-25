#!/bin/bash
#
# 01-b12-lancia.sh — gira SUL SERVER.  B12: la certificazione dei banchi.
#
#   bash /media/REMOTIX/src/01-b12-lancia.sh              i guasti leggeri
#   bash /media/REMOTIX/src/01-b12-lancia.sh B4 B9 C2     solo questi
#   bash /media/REMOTIX/src/01-b12-lancia.sh tutti        anche quelli che
#                                                         ricostruiscono
#   bash /media/REMOTIX/src/01-b12-lancia.sh elenco       il catalogo
#   bash /media/REMOTIX/src/01-b12-lancia.sh registro     chi e' certificato
#
# ---------------------------------------------------------------------------
# ⛔ IL GIRO E' TRE ESECUZIONI, NON UNA — e l'ordine non e' negoziabile
#
#   1. SANO    il banco gira sul codice buono e **dev'essere verde**.  ⛔ Senza
#              questo passo, «e' diventato rosso» non vuol dire niente: un banco
#              gia' rosso lo sarebbe anche col guasto, e la certificazione
#              sarebbe una tautologia;
#   2. GUASTO  si innesta il guasto e il banco **deve diventare rosso**, ⛔ **e
#              la sua uscita deve nominare la cosa giusta**: un guasto che rompe
#              la compilazione rende rosso qualunque banco e certifica ZERO;
#   3. RISANO  si toglie il guasto e il banco **deve tornare verde**.  ⛔ Senza,
#              «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo
#              stesso aspetto — e il guasto resta addosso al codice per il
#              prossimo che passa.
#
# ⭐ Il VERDETTO non sta qui: sta in `01-b12-guasti.py --giudica`, che vede i
#    tre passi insieme.  Questo script raccoglie **numeri**, non giudizi (B0.4).
#
# ---------------------------------------------------------------------------
# ⛔ LE USCITE SI CATTURANO DENTRO LE VIRGOLETTE, MAI ATTORNO A `enter.sh`
#
# Serve leggere l'uscita del banco per cercarci la marca.  ⛔ E una redirezione
# **attorno** a `enter.sh` si porta via la richiesta di password di sudo, e lo
# script resta ad aspettare una domanda che nessuno vede — tre volte in una sera
# il 10 agosto 2026.  Quindi ogni banco si lancia come
# `enter.sh --root "python3 … > file 2>&1"`, e il file lo si legge dopo.
#
# ⚠ Da cui una conseguenza: i banchi si lanciano **chiamando il loro programma**,
#   non il loro `01-bX-lancia.sh` — quelli girano fuori dal contenitore e non si
#   possono redirigere.  L'accensione del server la fa questo script, con la
#   stessa riga di comando che usano loro.
#
# ⛔⭐ E DUE BANCHI FANNO ECCEZIONE, PERCHE' LA REGOLA QUI SOPRA E' ANCHE LA
#     RADICE DI QUASI TUTTI I FALSI ROSSI DI OGGI — 11 agosto 2026, sera.
#
# **C2** e **B8** si lanciano dal loro `01-b*-lancia.sh`.  ⚠ Non e' una deroga
# comoda: sono i due banchi la cui scena non sta in una riga di comando — C2
# vuole il server acceso per due prove e spento per due, B8 vuole **due vite del
# server** (la persistenza del ban vuole un riavvio), la lettura della pagina e
# uno sblocco su un ban vero.  ⛔ Riscrivere quelle sequenze qui vuol dire
# tenerne due copie, e la seconda invecchia: e' esattamente quel che e' successo
# a B8, il cui giro «sano» sotto B12 usciva rosso su otto punti che parlavano di
# questo file e non del banco.
# ⭐ La cucitura e' la stessa nei due casi: niente redirezione attorno al
#    lanciatore, e la MARCA si legge dal file che il banco scrive da se'.
#
# ---------------------------------------------------------------------------
# ⛔⭐ IL BERSAGLIO SI DICHIARA — difetto **D6**, curato il 12 agosto 2026.
#
#   B12_BERSAGLIO=innesto   (predefinito)  `bsslserver`, il server di ngtcp2
#                                          con l'innesto RCP dentro
#   B12_BERSAGLIO=prodotto                 `remotix`, il prodotto vero
#
# ⛔ PERCHE' ERA UN DIFETTO, E NON UNA COMODITA' MANCANTE.
#
# Fino a stamattina qui c'era `SERVER=".../examples/bsslserver"` **scritto in
# chiaro** — mentre la porta era gia' configurabile con `B12_PORTA`.  ⇒ Questo
# orchestratore sapeva accendere **una scena sola**, e da li' due conseguenze
# che si sono viste tutt'e due:
#
#   · **B13 si certificava solo dal proprio script «sera»**
#     (`01-b13-sera-certifica.sh`), che rifa' lo STESSO ciclo con lo STESSO
#     guasto contro il prodotto — cioe' due strumenti per una cosa sola, e il
#     secondo destinato a invecchiare (e' la ragione per cui B8 e C2 si lanciano
#     dai loro lanciatori invece che da una copia della loro sequenza);
#   · **P1, P5 e P5R stanno fuori di qui** e certificano il prodotto per conto
#     loro.
#
# ⛔⭐ E LA PROVA CHE IL DIFETTO MORDEVA E' UN NUMERO, non un ragionamento:
#     sotto B12 il giro **sano** di B13 usciva **1** — rosso su `B13.4`, *«la
#     pagina servita in TCP»* — perche' B12 lo puntava sull'**innesto**, che la
#     pagina non la serve.  Contro il **prodotto** lo stesso identico giro esce
#     **3**, che e' l'atteso scritto nel catalogo.
#     ⇒ *Il numero era giusto e la SCENA era sbagliata.*  ⚠ E chi avesse curato
#       il numero — allargando `atteso_sano` finche' tornava — avrebbe scritto
#       nel catalogo che un rosso e' normale.
#
# ⛔ DA CUI LA SECONDA META' DELLA CURA, che vale piu' della prima: **ogni riga
#    di registro dice adesso quale scena ha misurato** (`--scena`, campo
#    `scena` in `01-b12-registro.jsonl`).  Senza, un domani due righe con lo
#    stesso nome e due scene diverse avrebbero lo stesso aspetto — che e' la
#    forma **E8** («vuoto» e «proibito» si leggono uguali) applicata al
#    registro, dentro lo strumento che esiste per non far credere niente a
#    nessuno.
#
# ⚠ E LA STRADA E' QUELLA GIA' IN CASA, non una seconda: `01-p1-prodotto.sh` si
#   lascia spostare con `SORG=` e `PORTA=`, `01-b0-terreno.sh` prende
#   `{innesto|prodotto}` come argomento e `SORG=` come ambiente, e
#   `01-b13-sera-accendi.sh` ha gia' scritto **come** si accende il prodotto
#   (porta, certificati, pagina, file dei ban, socket).  Qui si mettono insieme.
#
# ⛔ QUEL CHE QUESTA CURA **NON** FA, detto qui invece che scoperto da un rosso:
#
#   · non insegna a **costruire** il prodotto.  I guasti «ricostruisce» vivono
#     tutti in `examples/rcp.c` e si compilano con `ninja`; il prodotto vuole
#     `costruisci.sh` (lo dice gia' la nota di B10 nel catalogo).  ⇒ Sulla scena
#     «prodotto» un guasto «ricostruisce» viene **rifiutato**, non tentato;
#   · non porta P1, P5 e P5R dentro l'orchestratore: quelli vogliono un
#     **browser vero**, che su questa macchina non c'e'.  Restano fuori, e
#     restano dichiarati.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE (B0.1, B0.3)
#
#  · la porta 7447 dev'essere libera all'inizio;
#  · ⛔ **B12 accende e spegne il server a ogni passo**, e questo azzera il conto
#    di §4.4-bis, che vive nel processo.  ⚠ Il comando di sblocco **esiste**
#    (`01-b8-sblocca.py` su `--comando-socket`) e B12 **non lo chiama**: lo
#    dichiara qui, perche' B0.3 vuole che si sappia quale delle due cure ha
#    rimesso in piedi la macchina;
#  · ⚠ e il guasto si toglie **anche se il giro muore**: il `trap` lo rimette a
#    posto e ricostruisce, perche' un server che mente non deve sopravvivere.
#    ⛔ *Fino all'11 agosto 2026 questa riga era falsa e il rilievo R12-A.6 l'ha
#    misurata: `ripulisci()` faceva `spegni` e `--togli` e **non chiamava mai
#    `ricostruisci`**.  Ctrl-C durante il passo 2/3 di B7 rimetteva a posto
#    `examples/rcp.c` e lasciava `build/examples/bsslserver` compilato col
#    `CONGEDO` tolto: sorgente sano e **binario bugiardo**.  Il banco dopo —
#    B6, che confronta i `#define` fra sorgente e copia compilata — li trovava
#    d'accordo e misurava un server che mente.  E' la trappola «il file c'e'» /
#    «il file e' quello che ho appena costruito», gia' pagata su B11.*
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
LIBS="$DENTRO/b2/ngtcp2/build/lib"
IND=192.168.0.2
# ⛔ LA PORTA SI PUO' SPOSTARE, E NON E' UN VEZZO — 11 agosto 2026.
#    Su questa macchina misura piu' di una persona alla volta, e un giro di
#    certificazione che si prende :7447 spegne la scena di chi sta misurando
#    accanto.  ⚠ Senza la variabile la porta resta 7447, cioe' quella di
#    «innesto» in `01-b0-bersaglio.sh`: un predefinito diverso qui vorrebbe dire
#    certificare su una scena che nessuno ha dichiarato.
PORTA=${B12_PORTA:-7447}
# ⛔ E B8 vuole DUE cose in piu' di ogni altro banco, perche' la sua scena e'
#    §4.4-bis: un file dei ban e un socket di comando tutti suoi.  ⚠ Il file dei
#    ban e' «lo stato che sopravvive di piu' fra tutti» (B0.2): condividerlo con
#    un altro giro vuol dire ereditarne i dodici ore di ban.
B8_BAN=${B12_B8_BAN:-$DENTRO/b12-b8-ban.txt}
B8_SOCK=${B12_B8_COMANDO:-$DENTRO/b12-b8-comando.sock}
UTENTE=prova
PAROLA=parola-di-prova
ESITI=$DENTRO/b12-esiti.jsonl
ESITI_FUORI=$FUORI/b12-esiti.jsonl
GUASTI=$DENTRO/01-b12-guasti.py

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔⭐ IL BERSAGLIO, DICHIARATO QUI E IN UN POSTO SOLO — difetto D6.
#     La ragione per esteso sta in testa a questo file; qui c'e' la scelta.
BERSAGLIO=${B12_BERSAGLIO:-innesto}
# ⛔ L'albero del prodotto si dichiara come in `01-p1-prodotto.sh` e in
#    `01-b0-terreno.sh`: su questa macchina di alberi con dentro un `remotix`
#    ce n'e' piu' d'uno (`[M]` cinque, 12 agosto 2026), e «il prodotto» senza
#    un percorso non e' un bersaglio.
SORG=${B12_SORG:-$FUORI/remotix}
DENTRO_SORG=${B12_DENTRO_SORG:-$DENTRO/${SORG#"$FUORI/"}}
case "$BERSAGLIO" in
innesto)
	SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
	# ⚠ I certificati dell'innesto li fa B2 e sono condivisi: `pagina.pem` e
	#   `sessione.pem` stanno gia' li', ed e' su quei due che il guasto di
	#   B13 lavora.
	CERT=${B12_CERT:-/media/REMOTIX/b2-certificati}
	CERT_FUORI=${CERT/#$DENTRO/$FUORI}
	SCENA="innesto — bsslserver (b2/ngtcp2/build/examples) :$PORTA su $IND"
	;;
prodotto)
	SERVER="$DENTRO_SORG/remotix"
	# ⛔ E i certificati del prodotto sono i SUOI, non quelli di B2: se li
	#    genera da se' alla prima accensione, ed e' la ragione per cui c'e'
	#    una «scaldata» prima del giro — `--verifica B13` guarda quei due
	#    file, e su una cartella vuota direbbe «non si leggono» invece di
	#    «la scena non e' ancora pronta».
	CERT=${B12_CERT:-$DENTRO/tmp/b12-prodotto-cert}
	CERT_FUORI=${CERT/#$DENTRO/$FUORI}
	SCENA="prodotto — remotix ($SORG) :$PORTA su $IND"
	;;
*)	ko "⛔ B12_BERSAGLIO=«$BERSAGLIO» non esiste: «innesto» o «prodotto»"
	exit 2 ;;
esac

log "⭐ La scena, dichiarata PRIMA di misurarla (B0.1) — difetto D6"
inf "bersaglio:    $BERSAGLIO"
inf "server:       $SERVER"
inf "certificati:  $CERT"
inf "porta:        $PORTA"
inf "⛔ e questa riga finisce nel registro, campo «scena»:"
inf "   $SCENA"

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
# ⛔⭐ IL TERRENO, PRIMA DI TUTTO — rilievo R12-A.46, 11 agosto 2026.
#
# B12 costruisce guasti e legge rossi.  ⛔ Ma un rosso vale solo se il verde da
# cui parte era su un server **che e' quello dichiarato**, e l'11 agosto due
# volte non lo era: l'innesto RCP sparito da `examples/` (R12-A.45) e l'utente
# `prova` che non lo creava nessuno (R12-A.44).
# ⚠ Nel primo caso la certificazione di B2 **e' passata lo stesso**, su un
#   server senza meta' del prodotto dentro — perche' la sua sonda legge i
#   parametri QUIC e di RCP non sa niente.
# ⭐ Qui si guarda prima di misurare, e si rifiuta: un giro di certificazione
#    su un terreno ignoto scrive nel registro una riga con una data, e quella
#    riga poi la si crede.
# ⛔ E IL TERRENO SI CHIEDE DEL BERSAGLIO GIUSTO — D6.  Fino a stamattina qui
#    c'era `01-b0-terreno.sh innesto` scritto in chiaro, come il server: un giro
#    puntato sul prodotto avrebbe verificato l'innesto e sarebbe partito lo
#    stesso, cioe' avrebbe controllato **una scena che non stava per misurare**.
#    ⚠ E `SORG=` glielo si passa, perche' anche lui ha piu' d'un albero da
#      giudicare e sceglierne uno di suo sarebbe una seconda verita'.
log "0. ⛔ Il terreno (B0.1): il server «$BERSAGLIO» e' quello che credo?"
if ! SORG="$SORG" bash "$FUORI/01-b0-terreno.sh" "$BERSAGLIO"; then
	ko "⛔ NON CERTIFICO NIENTE: il terreno non regge."
	ko "   ⚠ E NON scrivo nel registro — un giro che non ha misurato niente"
	ko "   non e' un giro con zero certificati."
	exit 2
fi

# ---------------------------------------------------------------------------
# ⛔ LA SENTINELLA: «vuoto» non e' «zero» — rilievo R12-A.7, e la cura era gia'
#    scritta in questa stessa cartella, in `01-b11-guasto.sh:92-129`.
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` diceva «porta
# libera» in tre casi opposti: la porta e' davvero libera · `ss` non c'e' nel
# contenitore · `enter.sh` non ha eseguito il comando.  ⛔ E in questo file
# quella riga stava **venticinque righe sotto il commento che descrive quella
# stessa trappola** — una sostituzione di comando attorno a `enter.sh`, che si
# porta via la richiesta di password di sudo, dentro il banco che esiste per
# certificare gli altri.
#
# ⭐ Qui il comando remoto stampa da se' il proprio stato d'uscita: se la riga
#    `B12-FINE` non arriva, il comando non e' arrivato in fondo — e questo si
#    distingue da «e' andato e non ha trovato niente».
#
# ⚠ E LA SOSTITUZIONE DI COMANDO RESTA, ED E' LECITA SOLO QUI SOTTO: la prima
#   chiamata di questo script — `bash "$ENTRA" --root "true"`, qui sopra — e'
#   quella che si prende la richiesta di password, e da li' in poi le
#   credenziali di sudo sono valide.  ⛔ Il divieto vale per le REDIREZIONI
#   attorno a `enter.sh` e per qualunque cattura fatta **prima** di quella
#   riga; catturare dopo e' quel che fa anche `01-b11-guasto.sh`.
# ⚠ E cosi' la misura non poggia piu' sul fatto che `enter.sh` propaghi il
#   codice d'uscita del comando che esegue, che nessuno ha mai verificato
#   (rilievo R5.21, ancora aperto).
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB12-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B12-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B12-FINE=')
	if [ -z "$stato" ]; then
		return 125   # il comando non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta.  0 = occupata (le righe in $CHI) · 1 = libera · 2 = non
# si sa, e ⛔ «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta() # $1 = "-ulnp" (UDP) oppure "-tlnp" (TCP)
{
	local opz=${1:--ulnp} st
	dentro "ss $opz"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss $opz» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO: `ss` stampa sempre almeno la
	#    propria intestazione.  Se non stampa niente non ha guardato niente, e
	#    uno strumento che non sa vedere quel che c'e' non puo' dire che manchi
	#    qualcosa (`REVIEWER.md` §1 domanda 5).
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss $opz» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

case "${1:-leggeri}" in
elenco)   bash "$ENTRA" --root "python3 $GUASTI --elenco"; exit 0 ;;
registro) bash "$ENTRA" --root "python3 $GUASTI --registro"; exit 0 ;;
leggeri)  # ⚠ E l'elenco predefinito e' del BERSAGLIO, non dello script: C2
          #   accende e spegne `bsslserver` da se' (`01-c2-lancia.sh`), quindi
          #   sulla scena «prodotto» misurerebbe l'innesto **mentre il registro
          #   direbbe «prodotto»** — che e' il difetto D6 al contrario.
          if [ "$BERSAGLIO" = prodotto ]; then SIGLE="B13"; else SIGLE="C2 B13"; fi ;;
tutti)    if [ "$BERSAGLIO" = prodotto ]; then SIGLE="B13"; else SIGLE="C2 B13 B7"; fi ;;
*)        SIGLE="$*" ;;
esac
inf "sigle da provare: $SIGLE"
# ⛔ E B9 E B4 NON SONO IN QUESTO ELENCO, e va detto invece di essere
#    dimenticato.
#
#    `01-b9-letture.py` legge `RCP.md`, e ⛔ **su questa macchina `RCP.md` non
#    c'e'**: qui arrivano i banchi, non i documenti.  Lanciandolo di qui esce 4
#    — «non ho potuto leggere i testi» — e la certificazione registrerebbe un
#    rosso della causa sbagliata, cioe' esattamente quel che B12 esiste per
#    impedire.
#
# ⛔ E B4 e' lo stesso caso, scoperto l'11 agosto 2026: `01-b4-lancia.py` e
#    `01-b4-registrazioni.py` **non stanno in `/srv/src`**, quindi
#    `prepara_copia()` non trova gli originali e il giro sano esce 2 —
#    «python3: can't open file».  *E' esattamente quel che il registro delle
#    21:19 ha annotato come «B4 non certificato»: un rosso che non parlava del
#    banco.*  ⭐ Tutt'e due si certificano **sulla macchina dove stanno i
#    documenti e i loro banchi**, con lo stesso `01-b12-guasti.py`:
#
#      python3 banchi/01-b12-guasti.py --verifica B9
#      python3 banchi/01-b12-copie/01-b9-letture.py      # dev'essere 0
#      python3 banchi/01-b12-guasti.py --applica  B9
#      python3 banchi/01-b12-copie/01-b9-letture.py      # dev'essere 3
#      python3 banchi/01-b12-guasti.py --togli    B9
#
#    e per B4, con `01-b12-copie/01-b4-lancia.py 01-b12-copie/b4-registrazioni`
#    al posto del lettore (0 → 1 → 0).
inf "⚠ B9 e B4 non sono fra queste: si certificano dove stanno i loro file"

# ---------------------------------------------------------------------------
# ⛔⭐ RILIEVO R12-A.31, 11 agosto 2026 — L'AVVERTENZA QUI SOPRA ERA UN
#     CONSIGLIO, E CHI LA IGNORAVA OTTENEVA UN ROSSO PULITO.
#
# `bash 01-b12-lancia.sh B4 B9 C2` stampava la riga qui sopra e **poi lanciava
# B9 lo stesso**.  `[M]` 11 agosto: B9 e' uscito **4** — «senza i testi non c'e'
# nessun inventario da verificare», perche' `RCP.md` **su questa macchina non
# esiste** — e il verdetto ha scritto **«B9 NON certificato»**.
#
# ⛔ E' la forma opposta del falso verde, ed e' altrettanto cara: un banco sano
#    marchiato come non certificato manda a cercare un difetto che non c'e', e
#    intanto tiene il conto delle certificazioni fermo per una ragione che non
#    e' del banco.  ⚠ Il registro se lo porta dietro con una data, e chi lo
#    rilegge fra un mese non ha modo di sapere che quel rosso parlava di un file
#    mancante.
#
# ⭐ La cura non e' ripetere l'avvertenza piu' forte: e' **guardare se i file su
#    cui la certificazione poggia ci sono**, e rifiutarsi.  «Non posso provarlo
#    qui» e «l'ho provato e non passa» sono due fatti diversi, e B12 esiste per
#    non confonderli — e' il rilievo R12-A.4 applicato a se stesso.
# ---------------------------------------------------------------------------
RIFIUTATE=""
RESTA=""
for S in $SIGLE; do
	# ⛔⭐ E QUI C'ERA UN `2>/dev/null` **ATTORNO** A `enter.sh` — misurato la
	#     sera dell'11 agosto 2026, ed e' la stessa trappola che questo file
	#     descrive in cima, per la QUINTA volta.
	#
	# `enter.sh` chiama `sudo -v -S -p Password`: la richiesta esce su
	# **stderr** e la risposta si legge da stdin.  Buttando via stderr, la
	# richiesta non arriva a nessuno — e chi lancia il giro da un'altra
	# macchina non ha modo di rispondere a una domanda che non vede.
	# `[M]` `ps` sul server: `sudo -v -S -p Password sudo:` fermo, e sotto di
	# lui `enter.sh --root python3 … --provabile B8 2>/dev/null`, con l'intero
	# giro di certificazione fermo al passo 0 di 3.
	# ⚠ Da un terminale interattivo il difetto e' invisibile finche' il credito
	#   di sudo regge: si vede solo quando scade, cioe' sui giri lunghi — che
	#   sono esattamente quelli che costano di piu' da rifare.
	# ⭐ Il `2>/dev/null` DENTRO le virgolette resta: quello butta lo stderr
	#    del programma remoto, che e' quel che si voleva.
	MANCA=$(bash "$ENTRA" --root \
	    "python3 $GUASTI --provabile $S 2>/dev/null" \
	    | tr -d '\r' | sed -n 's/^MANCA //p' | tr '\n' ' ')
	# ⛔⭐ E LA SECONDA DOMANDA E' NUOVA — D6: «si prova su QUESTA SCENA?»
	#
	# La prima guarda se i file ci sono su questa macchina (R12-A.31).  Questa
	# guarda se il guasto ha senso contro questo bersaglio: i guasti «ricostruisce»
	# vivono in `examples/rcp.c` e si compilano con `ninja`, cioe' **fanno parte
	# dell'innesto**.  ⛔ Innestarne uno mentre si misura il prodotto lascerebbe
	# il prodotto intatto: il banco resterebbe verde e chi legge concluderebbe
	# «il banco non vede il guasto» — l'accusa esattamente opposta, che e' la
	# trappola n.2 del catalogo.
	# ⚠ E si rifiuta PRIMA di spendere il giro sano, come l'altra.
	COSTA_S=$(python3 "$FUORI/01-b12-guasti.py" --costa "$S" | tr -d '\r' | tail -1)
	if [ "$BERSAGLIO" = prodotto ] && [ "$COSTA_S" = ricostruisce ]; then
		ko "⛔ «$S» NON si prova sulla scena «prodotto»: il suo guasto e' di"
		ko "   tipo «ricostruisce», cioe' vive in examples/rcp.c e si compila"
		ko "   con ninja — e' un guasto dell'INNESTO."
		ko "   ⚠ Innestandolo qui il prodotto resterebbe sano e il banco verde:"
		ko "     «il banco non vede il guasto» invece di «il guasto non c'era»."
		RIFIUTATE="$RIFIUTATE $S"
	elif [ -n "$MANCA" ]; then
		ko "⛔ «$S» NON si prova qui: manca $MANCA"
		ko "   Non e' «non certificato»: e' «non certificabile su questa"
		ko "   macchina».  Si certifica dove stanno i suoi file."
		RIFIUTATE="$RIFIUTATE $S"
	else
		RESTA="$RESTA $S"
	fi
done
if [ -n "$RIFIUTATE" ]; then
	inf "⛔ rifiutate qui:$RIFIUTATE   ·   restano:${RESTA:- —}"
	SIGLE=$RESTA
fi
if [ -z "${SIGLE// /}" ]; then
	ko "⛔ nessuna sigla provabile su questa macchina: non lancio niente."
	ko "   ⚠ E NON scrivo nel registro: un giro che non ha provato niente"
	ko "   non e' un giro con zero certificati."
	exit 0
fi

rm -f "$ESITI_FUORI"

PID=""
accendi() # $1 = base del certificato (sessione | pagina), $2 = etichetta,
          # $3 = su quale indirizzo legarsi (opzionale, predefinito $IND)
{
	local base=$1 et=$2 lega=${3:-$IND}
	shift 3 2>/dev/null || shift $#
	local extra="$*"   # opzioni in piu' per il server (B8 vuole il socket)
	# ⛔⭐ PERCHE' L'INDIRIZZO E' UN PARAMETRO — rilievo R12-A.39, 11 agosto 2026.
	#
	# Tutti i banchi si accontentano di un server legato a $IND.  ⛔ B8 no: la
	# sua scena E' §4.4-bis, che conta i tentativi **per indirizzo di
	# provenienza**, e per vedere due bilanci separati servono DUE provenienze
	# — 127.0.0.1 e 192.168.0.2.  Con il server legato al solo 192.168.0.2, da
	# 127.0.0.1 non risponde nessuno.
	# ⚠ `[M]` 11 agosto: B8 e' uscito **2** — «da 127.0.0.1 non si arriva a
	#   ECCOMI» — e non 1.  ⭐ Cioe' si e' RIFIUTATO di misurare invece di
	#   misurare meta' scena e chiamarla intera: e' il comportamento giusto, ed
	#   e' anche il motivo per cui questo difetto si e' visto subito.
	rm -f "$FUORI/b12-$et.log" "$FUORI/b12-$et.pid"
	# ⛔⭐ E LA RIGA DI COMANDO E' DEL BERSAGLIO, NON DI QUESTO SCRIPT — D6.
	#
	# I due server non si accendono nello stesso modo, e fingere che sia lo
	# stesso e' precisamente il difetto: `bsslserver` prende i due certificati
	# come argomenti posizionali e non serve nessuna pagina; `remotix` li
	# **genera da se'** dentro `--certificati`, vuole `--pagina`, e ha un file
	# dei ban e un socket di comando.  ⚠ La forma di questa seconda riga non e'
	# inventata qui: e' quella di `01-b13-sera-accendi.sh`, che l'ha misurata.
	# ⛔ E il file dei ban e il socket sono **di questo giro**: §4.4-bis conta
	#    per indirizzo e un ban dura dodici ore — ereditare quello di un altro
	#    giro vorrebbe dire misurare i suoi tentativi.
	if [ "$BERSAGLIO" = prodotto ]; then
		bash "$ENTRA" --root \
			"mkdir -p $CERT $DENTRO/tmp; nohup $SERVER --indirizzo $lega --nome $IND --porta $PORTA --certificati $CERT --pagina $DENTRO_SORG/pagina.html --ban-file $DENTRO/tmp/b12-prodotto-ban --comando-socket $DENTRO/tmp/b12-prodotto.sock --parlantina $extra < /dev/null > $DENTRO/b12-$et.log 2>&1 & echo \$! > $DENTRO/b12-$et.pid"
	else
		bash "$ENTRA" --root \
			"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $extra $lega $PORTA $CERT/$base.key $CERT/$base.pem < /dev/null > $DENTRO/b12-$et.log 2>&1 & echo \$! > $DENTRO/b12-$et.pid"
	fi
	sleep 2
	PID=$(cat "$FUORI/b12-$et.pid" 2>/dev/null)
	# ⛔ `/proc`, non `kill -0`: il server e' di root e questo script no.
	if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
		ko "il server non e' partito ($base):"
		[ -f "$FUORI/b12-$et.log" ] && sed 's/^/        /' "$FUORI/b12-$et.log"
		PID=""
		return 1
	fi
	ok "server «$BERSAGLIO» acceso col certificato «$base», PID $PID"
	# ⛔⭐ E SUL PRODOTTO «IL PROCESSO E' VIVO» NON BASTA — B0.7, e qui morde.
	#
	# §2.4 vuole DUE ascoltatori sulla stessa porta: UDP per RCP e TCP per la
	# pagina.  ⛔ B13.4 — *«la pagina servita in TCP»* — e' esattamente la
	# proprieta' per cui questo bersaglio esiste: se il TCP non c'e' ancora, il
	# banco esce rosso e il rosso parla dell'attesa, non del server.
	# ⚠ Un marcatore, non un `sleep`: si guarda la porta, non l'orologio.
	if [ "$BERSAGLIO" = prodotto ]; then
		local g=0 n=0
		while [ "$g" -lt 40 ]; do
			[ -d "/proc/$PID" ] || break
			if dentro "ss -tuln"; then
				n=$(printf '%s\n' "$USCITA" | grep -c ":$PORTA ")
				[ "$n" -ge 2 ] && break
			fi
			sleep 0.5; g=$((g + 1))
		done
		if [ "$n" -lt 2 ]; then
			ko "⛔ su :$PORTA ci sono $n ascoltatori e ne servono DUE (§2.4)"
			ko "   ⚠ non lancio il banco: un rosso raccolto adesso parlerebbe"
			ko "     di questa attesa, non del server"
			[ -f "$FUORI/b12-$et.log" ] && tail -20 "$FUORI/b12-$et.log" | sed 's/^/        /'
			return 1
		fi
		ok "e ascolta in UDP e in TCP su :$PORTA ($n righe di «ss»)"
	fi
	return 0
}

spegni()
{
	[ -n "$PID" ] || return 0
	bash "$ENTRA" --root "kill $PID 2>/dev/null || true"
	local g=0
	while [ -d "/proc/$PID" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g + 1)); done
	PID=""
}

ricostruisci()
{
	# ⛔⭐ E SUL PRODOTTO QUESTA FUNZIONE NON SA COSTRUIRE NIENTE, E LO DICE —
	#     D6, 12 agosto 2026.
	#
	# `ninja -C b2/ngtcp2/build bsslserver` costruisce l'INNESTO.  Il prodotto
	# si costruisce con `costruisci.sh` (`GEMELLO=nessuno bash …`), e il
	# catalogo lo scrive gia' nella nota di B10.  ⛔ Chiamare `ninja` qui e
	# leggerne lo zero vorrebbe dire dichiarare ricostruito un binario che
	# nessuno ha toccato — e il giro «col guasto» misurerebbe **il binario di
	# prima**, cioe' il difetto n.3 di `01-b12-guasti.py` al suo peggio.
	# ⚠ Si sbaglia per rifiuto, mai per silenzio: nessun guasto «ricostruisce»
	#   arriva fin qui, perche' piu' sotto la scena «prodotto» li rifiuta prima
	#   di spendere il giro sano.  Questa riga e' la seconda rete.
	if [ "$BERSAGLIO" = prodotto ]; then
		# ⚠ E niente apici inversi dentro le virgolette doppie: la shell li
		#   ESEGUE, ed e' la trappola che questo stesso albero ha gia' pagato
		#   in «attrezzi-allinea-innesto.sh» e in «01-b13-sera-certifica.sh».
		ko "⛔ non so costruire il PRODOTTO: «ninja» costruisce l'innesto, e il"
		ko "   prodotto vuole «GEMELLO=nessuno bash $DENTRO_SORG/costruisci.sh»."
		ko "   ⛔ E non ricostruisco «per sicurezza»: un binario non toccato e"
		ko "     un binario ricostruito hanno lo stesso aspetto, e il giro col"
		ko "     guasto misurerebbe quello di prima."
		return 1
	fi
	rm -f "$FUORI/b12-compila.log"
	if ! bash "$ENTRA" --root \
		"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b12-compila.log 2>&1"; then
		ko "⛔ la compilazione e' fallita:"
		[ -f "$FUORI/b12-compila.log" ] && tail -20 "$FUORI/b12-compila.log" | sed 's/^/        /'
		# ⛔ E questo NON e' «il banco e' diventato rosso»: e' che non c'e'
		#    nessun binario da provare.  Chi non distingue le due cose
		#    certifica dodici banchi con una compilazione rotta.
		return 1
	fi
	ok "ricostruito"
	return 0
}

# ⛔ La ripulitura vale piu' del verdetto: un guasto lasciato addosso al codice
#    avvelena ogni misura successiva, e nessuno sapra' che c'era.
#
# ⛔ E RIMETTERE IL SORGENTE NON BASTA: VA RICOSTRUITO — rilievo R12-A.6.
#
#    `--togli` rimette a posto `examples/rcp.c`; il binario in
#    `build/examples/bsslserver` resta quello **compilato col guasto dentro**.
#    Sorgente sano e binario bugiardo e' peggio di tutt'e due guasti: il banco
#    successivo legge il sorgente, lo trova pulito — B6 confronta proprio i
#    `#define` fra sorgente e copia compilata e li trova d'accordo — e misura
#    un server che mente.  ⚠ E' la stessa forma pagata su B11 il 10 agosto
#    2026: «il file c'e'» e «il file e' quello che ho appena costruito».
SIGLA_APERTA=""
COSTA_APERTA=""
# ⛔ E LE DUE VARIABILI SI AZZERANO SOLO QUANDO IL LAVORO E' FATTO: una
#    ripulitura che si dichiara riuscita e' peggio di una che non c'e', perche'
#    il `trap` non ci riprova.  ⭐ Questa funzione e' anche il passo 3/3 del
#    giro: la ripulitura e il ritorno al sano sono la stessa operazione, e
#    tenerne due copie voleva dire che una delle due sarebbe invecchiata.
ripulisci()
{
	spegni
	[ -n "$SIGLA_APERTA" ] || return 0
	local st=0
	log "⛔ Si toglie il guasto «$SIGLA_APERTA»"
	bash "$ENTRA" --root "python3 $GUASTI --togli $SIGLA_APERTA --certificati $CERT"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ IL GUASTO NON E' STATO TOLTO: si rilancia a mano"
		ko "   ⛔ e il binario resta quello col guasto dentro: NON SI MISURA"
		ko "     niente su questa macchina finche' non e' rimesso a posto"
		return "$st"
	fi
	# ⛔ E ADESSO IL BINARIO.  Senza questa riga il commento in cima a questo
	#    file era falso, e lo e' stato per un giorno intero.
	if [ "$COSTA_APERTA" = ricostruisce ]; then
		inf "⚠ il sorgente e' sano ma il binario e' ancora quello col guasto:"
		inf "  si ricostruisce, o resta un server che mente"
		if ricostruisci; then
			ok "⭐ sorgente sano E binario ricostruito: niente sopravvive al giro"
		else
			ko "⛔ LA RICOSTRUZIONE E' FALLITA: il binario in"
			ko "   $SERVER porta ancora il guasto «$SIGLA_APERTA»."
			ko "   ⛔ Ogni misura fatta su questa macchina da adesso e' avvelenata."
			return 1
		fi
	fi
	SIGLA_APERTA=""; COSTA_APERTA=""
	return 0
}
trap ripulisci EXIT

# ---------------------------------------------------------------------------
# gira <sigla> <passo>   → scrive una riga in $ESITI
#
# ⛔ Ogni banco ha la sua riga di comando, e ciascuna e' quella che il banco
#    userebbe da se': un banco lanciato in modo diverso da come vive non e'
#    quel banco.
gira()
{
	local sigla=$1 passo=$2 u=0 marca="" uscita_file="$DENTRO/b12-uscita.txt"
	local fuori_file="$FUORI/b12-uscita.txt"
	rm -f "$fuori_file"
	case "$sigla" in
	B4)
		bash "$ENTRA" --root \
			"python3 $DENTRO/01-b12-copie/01-b4-lancia.py $DENTRO/01-b12-copie/b4-registrazioni > $uscita_file 2>&1"
		u=$? ;;
	B9)
		bash "$ENTRA" --root \
			"python3 $DENTRO/01-b12-copie/01-b9-letture.py > $uscita_file 2>&1"
		u=$? ;;
	C2)
		# ⚠ C2 vuole il server acceso per due scene e spento per due: il suo
		#   `01-c2-lancia.sh` lo sa fare, e gira FUORI dal contenitore.  Qui si
		#   accetta di non poter redirigere e si legge la marca dagli esiti su
		#   file, che C2 scrive per conto suo.
		bash "$FUORI/01-c2-lancia.sh" tutto "$DENTRO/01-b12-copie/01-c2-diagnosi.py"
		u=$?
		cp -f "$FUORI/c2-esiti.json" "$fuori_file" 2>/dev/null ;;
	B13)
		# ⛔ QUI C'ERA `[ "$passo" = guasto ] && base=pagina`, ED ERA CODICE
		#    MORTO — rilievi R12-A.1 e R12-A.2.  Morto due volte:
		#      · non ci si arrivava mai (il guasto era di tipo
		#        `riga-di-comando`, `--applica` lo rifiutava e il giro faceva
		#        `continue` prima del passo 2/3);
		#      · e se ci si fosse arrivati avrebbe costruito **il guasto
		#        sbagliato**: `proprieta_1` confronta le impronte dei due FILE
		#        su disco, non il certificato presentato sul filo, quindi
		#        accendere il server con `pagina.pem` non le avrebbe fatte
		#        combaciare e la marca non sarebbe uscita mai.
		# ⭐ Adesso il guasto e' sui due file (tipo `copia-di-file`) e il server
		#    si accende sempre con `sessione`, come vive.
		# ⛔⭐ E LA COPIA COMPILATA SI DICHIARA, ED E' DIVERSA PER SCENA — D6.
		#
		# B13.6 chiede «sto leggendo il codice che e' DENTRO il binario che ho
		# appena acceso?», e la risposta cambia col bersaglio: sull'innesto il
		# server nasce da `b2/ngtcp2/examples/rcp.c`, sul prodotto da
		# `remotix/rcp.c`.  ⛔ Passargliene una sola — o quella sbagliata —
		# vuol dire farlo rispondere a «sto leggendo *un* rcp.c?», che e' la
		# domanda piu' debole (`LEZIONI.md` §1.9, ottava veste, citata dal
		# banco stesso).
		# ⚠ La forma delle tre opzioni non e' inventata qui: e' quella che
		#   `01-b13-sera-certifica.sh` ha misurato contro il prodotto — lo
		#   stesso giro che e' uscito 3, cioe' l'atteso del catalogo.
		local b13_comp b13_fonti
		if [ "$BERSAGLIO" = prodotto ]; then
			b13_comp=$DENTRO_SORG/rcp.c
			b13_fonti="$DENTRO_SORG/certificati.c $DENTRO_SORG/main.c $DENTRO_SORG/rcp.c"
		else
			b13_comp=$DENTRO/b2/ngtcp2/examples/rcp.c
			b13_fonti="$DENTRO/rcp/rcp.c $DENTRO/01-b3-rcp-innesta.py $DENTRO/01-b2-ngtcp2-wt-innesta.py"
		fi
		accendi sessione "b13-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b13-proprieta.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --certificati $CERT --prodotti $DENTRO --codice $DENTRO/rcp/rcp.c --codice-compilato $b13_comp --fonti-codice $b13_fonti > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	B2)
		# ⛔ La sonda del trasporto legge i parametri che il server DICHIARA
		#    nella stretta di mano — fra cui il credito di stream
		#    unidirezionali, che §2.3 vuole «almeno 16».  ⚠ Il tetto
		#    d'inattivita' atteso e' quello con cui `accendi` lancia il server
		#    (`--timeout=120s`), non i 30 s predefiniti della sonda: passarlo
		#    e' la differenza fra misurare e far tornare i conti.
		accendi sessione "b2-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b2-sonda-trasporto.py --bersaglio innesto --indirizzo $IND --porta $PORTA --etichetta b12-$passo --idle-atteso 120000 > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	B3)
		# ⛔ B3 E' DUE CONNESSIONI, e la seconda e' tutto il banco.
		#    `LEZIONI.md` §2.1: in v1 il server moriva **alla seconda**, e una
		#    prova a collegamento singolo resta verde per sempre.  ⭐ Qui si
		#    riproduce quel che fa `01-b3-lancia.sh` ai punti 1 e 2: la prima
		#    connessione, poi la seconda **dopo che la prima si e' chiusa**.
		# ⚠ Il terzo giro (GIA_ATTIVA_REMOTA, le due vive insieme) sta in un
		#   file suo e NON e' coperto da questa certificazione: si dichiara
		#   invece di lasciar credere che il denominatore sia quello intero.
		accendi sessione "b3-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b3-cliente.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registra $DENTRO/b12-b3-uno.rcpreg > $uscita_file 2>&1"
			u=$?
			inf "prima connessione: uscita $u"
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b3-cliente.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registra $DENTRO/b12-b3-due.rcpreg >> $uscita_file 2>&1"
			local u2=$?
			inf "SECONDA connessione: uscita $u2"
			# ⛔ L'esito del passo e' il PEGGIORE dei due: se la prima passa e
			#    la seconda no, il banco dev'essere rosso — e' esattamente il
			#    caso per cui B3 esiste.
			[ "$u2" -eq 0 ] || u=$u2
		fi
		spegni ;;
	B5)
		accendi sessione "b5-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b5-violazioni.py --bersaglio innesto --indirizzo $IND --porta $PORTA > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	B8)
		# ⛔⭐ B8 SI LANCIA DAL SUO LANCIATORE, ED E' LA RIGA PIU' IMPORTANTE
		#     DI QUESTO FILE — 11 agosto 2026, sera.
		#
		# Fino a stasera qui c'era una COPIA della sequenza di
		# `01-b8-lancia.sh`: accensione, scaldata, sei blocchi corti con lo
		# sblocco in mezzo, verdetto.  ⛔ Una copia scritta bene, e incompleta
		# in tre punti che il catalogo aveva gia' misurato: le **due vite del
		# server** (senza riavvio la persistenza del ban — invariante I7 —
		# non si prova), la **lettura della pagina** (§4.4-bis punto 1) e lo
		# **sblocco su un ban VERO** (senza, «tolto» e «non c'era» hanno lo
		# stesso aspetto).  ⇒ Il giro sano usciva rosso su otto punti, e
		# ⛔ **nessuno degli otto parlava di B8**: parlavano di quel che
		# questo orchestratore non gli dava.
		#
		# ⭐ La cura non e' completare la copia — sarebbe una quarta stesura
		#    della stessa sequenza, cioe' la radice dei falsi rossi di oggi —
		#    ma chiamare il lanciatore, che quella sequenza ce l'ha scritta,
		#    commentata e gia' pagata.  ⚠ E' quel che C2 fa da sempre, poche
		#    righe piu' su, per la stessa ragione: certi banchi non stanno in
		#    una riga di comando.
		#
		# ⛔ TRE CUCITURE, E CIASCUNA HA UNA RAGIONE:
		#
		#   · niente redirezione ATTORNO al lanciatore: dentro chiama
		#     `enter.sh`, e una redirezione si porterebbe via la richiesta di
		#     password di sudo.  ⭐ La marca si legge dal file che il verdetto
		#     di B8 scrive da se' (`b8-verdetto-<bersaglio>.txt`), esattamente
		#     come per C2;
		#   · `B8_NON_RICOSTRUIRE=1`: il lanciatore, sull'innesto, rimette gli
		#     innesti e ricompila — e ⛔ questo CANCELLEREBBE il guasto da
		#     `examples/rcp.c` al passo 2/3, lasciando il banco verde su un
		#     server sano.  Restano la verifica md5 del binario e il rifiuto
		#     di un binario piu' vecchio dei sorgenti;
		#   · porta, file dei ban e socket **spostati**: due giri sulla stessa
		#     macchina non condividono mai il file dei ban (§4.4-bis conta per
		#     indirizzo, e un ban dura dodici ore).
		# ⛔⭐ PERCHE' 10 E NON 6 — 12 agosto 2026, sera.  ⚠ CHI LO RIABBASSA
		#     PER FAR PRIMA RIMETTE IN PIEDI UN FALSO ROSSO SULLA SICUREZZA.
		#
		# Il predefinito era **6**, cioe' `6 × PER_CASO(2)` = **12 campioni per
		# caso**.  ⛔ Con 12 campioni la coppia «inesistente − sbagliata» — che
		# e' **l'unica delle tre che porta il segreto** che §4.4 vieta di far
		# trapelare (se un nome utente esista) — si separa **per caso**, e non
		# per un difetto del server: a spostare quei tempi e' la randomizzazione
		# di `pam_faildelay` in `libpam`, che B8 dichiara come `[?]` aperta.
		#
		# ⛔ IL CASO CONCRETO, `[M]` 12 agosto 2026, giro di B8 a 6 blocchi:
		#
		#     inesistente − sbagliata   **-409 ms   [-677; -8]**   ris. ±335 ms
		#     ⇒ l'intervallo NON contiene lo zero  ⇒  **SI DISTINGUONO**
		#
		#    cioe' un **ROSSO PIENO sulla proprieta' di sicurezza**, che B12
		#    leggerebbe come *«il guasto e' rimasto addosso al codice»* — mentre
		#    il terreno dice di no.  ⚠ E l'estremo che decide e' **-8 ms**: la
		#    separazione e' passata dalla parte sbagliata dello zero per otto
		#    millisecondi su una risoluzione di ±335.
		#
		# ⭐ E CHE NON SIA UN CASO ISOLATO LO DICE IL DENOMINATORE, non
		#    l'aneddoto.  `[M]` sei giri a 6 blocchi della stessa sera, stessa
		#    scena, stesso innesto (`cert-b8.log`, `b12-b8.log`, tre passi
		#    ciascuno) — la stessa coppia, sullo stesso server sano:
		#
		#      -197.0  [-349.9; +163.7]  ±256.8      +17.2  [-374.0; +477.8]  ±425.9
		#       +24.5  [-513.2; +301.1]  ±407.1     -119.1  [-604.1; +324.7]  ±464.4
		#      -160.9  [-521.2; +254.9]  ±388.1     -158.2  [-439.6; +274.6]  ±357.1
		#
		#    ⛔ La stima puntuale **vaga di ±400 ms** mentre la semiampiezza vale
		#       ~±380: le due grandezze sono **la stessa**, quindi lo zero sta
		#       sul bordo e prima o poi ci esce.  Su sette giri a 12 campioni ne
		#       e' uscito **uno**, ed e' esattamente il tasso che questi numeri
		#       prevedono.  ⇒ Non era sfortuna: era il numero di campioni.
		#
		# ⭐ A **10 blocchi** (= 20 campioni per caso) `[M]` la coppia del
		#    segreto **non si separa in nessuno dei tre passi** — sano, guasto,
		#    risanato — e il verdetto torna a essere quel che deve: `SOSPESO`
		#    oppure `indistinguibili`, mai `SI DISTINGUONO`.
		#
		# ⚠ E QUEL CHE 10 **NON** COMPRA, detto invece che sottinteso: non
		#   compra il verde.  ±50 ms (`RISOLUZIONE_VOLUTA`) resta irraggiungibile
		#   — B8 stesso stampa che con questo rumore servirebbero **~871-1036
		#   campioni per caso** — quindi il verdetto onesto a 20 campioni resta
		#   `SOSPESO`.  ⭐ Ma il SOSPESO e' l'esito giusto («guardare meno allarga
		#   l'intervallo e porta al sospeso, non al verde»), mentre il
		#   `SI DISTINGUONO` di prima era un'**accusa** — e fra i due sbagli
		#   quello che si paga e' l'accusa.
		#
		# ⛔ IL PREZZO, dichiarato e contato con la formula che stampa
		#    `01-b8-lancia.sh` stesso (`BLOCCHI*6*4/60+2` … `BLOCCHI*6*6/60+4`):
		#
		#      6 blocchi   4-7 minuti per passo    · 33 autenticazioni fallite
		#     10 blocchi   6-10 minuti per passo   · 49 autenticazioni fallite
		#
		#    ⇒ **+2/3 minuti per passo, ×3 passi: +6/9 minuti in tutto.**  ⚠ E le
		#    autenticazioni fallite in piu' non toccano il bilancio di §4.4-bis:
		#    quello e' **per blocco** (2 per indirizzo, soglia 3) e si sblocca fra
		#    un blocco e l'altro — piu' blocchi vuol dire piu' sblocchi, non un
		#    conto piu' alto.
		#
		# ⛔ Se un giorno serve piu' corto, si abbassa con `B12_B8_BLOCCHI=…`
		#    **dichiarandolo nel rapporto**, e non si tocca questa riga: il
		#    predefinito e' il numero che regge senza che nessuno ci pensi.
		local blocchi8=${B12_B8_BLOCCHI:-10}
		inf "⭐ B8 si lancia dal SUO lanciatore ($blocchi8 blocchi): due vite"
		inf "   del server · la pagina del ban · lo sblocco su un ban vero."
		inf "   ⚠ Dura qualche minuto per passo, ed e' il prezzo di una"
		inf "   certificazione che copre la sequenza intera"
		inf "scena: porta $PORTA · ban $B8_BAN · comando $B8_SOCK"
		# ⛔ E il file del verdetto si BUTTA PRIMA, non dopo: quello del passo
		#    precedente farebbe cercare la marca nei numeri di un altro giro.
		rm -f "$FUORI/b8-verdetto-innesto.txt"
		BERSAGLIO=innesto \
		B8_NON_RICOSTRUIRE=1 \
		B8_PORTA="$PORTA" \
		B8_BAN="$B8_BAN" \
		B8_COMANDO="$B8_SOCK" \
			bash "$FUORI/01-b8-lancia.sh" "$blocchi8"
		u=$?
		cp -f "$FUORI/b8-verdetto-innesto.txt" "$fuori_file" 2>/dev/null ;;
	B6)
		# ⛔⭐ B6 SI PUO' CERTIFICARE, E L'OBIEZIONE IN CATALOGO NON REGGEVA
		#     — rilievo R12-A.32, 11 agosto 2026.
		#
		# La nota diceva: *«il guasto va innestato in `rcp/rcp.c` e non nella
		# copia di `examples/` — `01-b6-lancia.sh` ricopia il sorgente a ogni
		# giro e cancellerebbe il guasto, e il confronto fra i due `#define`
		# che B6 fa al passo 2 lo vedrebbe comunque»*.
		#
		# ⭐ Tutt'e due le meta' parlano di `01-b6-lancia.sh`, e **B12 non lo
		#    usa**: qui i banchi si chiamano dal loro programma (la ragione sta
		#    in testa a questo file — le uscite vanno catturate dentro le
		#    virgolette di `enter.sh`).  Ne' la ricopiatura ne' il confronto
		#    fra i `#define` girano da questa parte.
		#
		# ⚠ E VA DETTO CHE COSA QUESTA CERTIFICAZIONE **NON** COPRE, invece di
		#   lasciarlo credere: certifica `01-b6-tetti.py`, cioe' i casi sul
		#   filo.  Il confronto sorgente/binario e il richiamo allo sblocco di
		#   §4.4-bis stanno nel lanciatore e restano **non certificati**.
		#
		# ⛔ E i tetti del codice si LEGGONO, non si scrivono a mano: passare
		#    5000 al passo col guasto sarebbe mentire al banco proprio dove il
		#    guasto vive.
		local tc="" nome b
		for coppia in "CIAO:TETTO_CIAO" "CREDENZIALI:TETTO_CREDENZIALI" "ATTACCA:TETTO_ATTACCA"; do
			nome=${coppia%%:*}
			b=$(sed -n "s/^#define ${coppia##*:}[[:space:]]\{1,\}\([0-9]\{1,\}\).*/\1/p" \
			    "$FUORI/b2/ngtcp2/examples/rcp.c" | head -1)
			[ -n "$b" ] && tc="$tc${tc:+,}$nome=$b"
		done
		inf "tetti letti dal sorgente compilato: ${tc:-⛔ NESSUNO}"
		if [ -z "$tc" ]; then
			ko "⛔ non ho letto nessun tetto da examples/rcp.c: non lancio B6"
			ko "   ⚠ con i tetti ignoti il banco misurerebbe contro niente"
			u=99
		else
			accendi sessione "b6-$passo" || { u=99; }
			if [ "$u" -eq 0 ]; then
				bash "$ENTRA" --root \
					"python3 -u $DENTRO/01-b6-tetti.py --bersaglio innesto --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --fase sani --idle 120000 --tetti-codice $tc > $uscita_file 2>&1"
				u=$?
			fi
			spegni
		fi ;;
	B7)
		accendi sessione "b7-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b7-congedo.py --bersaglio innesto --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registro $DENTRO/b12-b7-$passo.log --pagina $DENTRO/01-b11-pagina.html > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	*)
		ko "⛔ non so come lanciare il banco «$sigla»: il guasto e' catalogato"
		ko "   ma non eseguito, e va detto invece di contarlo"
		return 9 ;;
	esac

	# ⛔ L'uscita del banco si mostra sempre, anche quando e' verde: un giro di
	#    certificazione in cui si vede solo il numero non permette a nessuno di
	#    accorgersi che il rosso era di un'altra causa.
	if [ -f "$fuori_file" ]; then
		tail -25 "$fuori_file" | sed 's/^/        /'
	else
		inf "⚠ nessuna uscita catturata per «$sigla» passo «$passo»: la marca"
		inf "  non si potra' cercare, e la certificazione lo contera'"
	fi
	printf '%s\n' "$u" > "$FUORI/b12-ultima-uscita.txt"
	inf "«$sigla» passo «$passo»: uscita $u"
	return "$u"
}

# ---------------------------------------------------------------------------
# ⛔ La marca si cerca QUI, in un posto solo, e con un `grep` che sa fallire.
# ⛔ E QUESTE DUE DOMANDE NON PASSANO DA `enter.sh`, ED E' LA TRAPPOLA CHE
#    QUESTO STESSO FILE DESCRIVE IN CIMA — pagata di nuovo il 10 agosto 2026,
#    dentro il banco che esiste per certificare gli altri.
#
#    `X=$(bash enter.sh --root "…")` e' una **sostituzione di comando attorno a
#    enter.sh**: si porta via la richiesta di password di sudo, e il giro resta
#    appeso per sempre su una domanda che nessuno vede.  Il giro delle 22:50 si
#    e' fermato esattamente li', subito dopo aver innestato il guasto — cioe'
#    **col guasto addosso al codice**, che e' il peggior punto in cui fermarsi.
#
# ⭐ La cura: il catalogo si interroga **fuori dal contenitore**.  `01-b12-*` e i
#    file di `$FUORI` sono gli stessi di `$DENTRO`, e python3 c'e' anche qui.
# ⛔ E LA MARCA SI CERCA IN TUTT'E TRE I PASSI, NON SOLO NEL GUASTO —
#    rilievo R12-A.3.  Il criterio ha due meta':
#
#      · l'uscita ROSSA deve nominare la marca;
#      · ⛔ e il giro SANO **non la deve gia' nominare**.
#
#    Qui la seconda meta' non c'era: `annota "$S" sano "$U" false` scriveva
#    `false` **a mano**, cioe' dichiarava senza guardare.  Cosi' B7, la cui
#    marca era «CONGEDO» — 37 volte nell'uscita sana — e' stato certificato il
#    10 agosto alle 21:19 senza che nessuno avesse verificato niente.
#    ⭐ La riga che chiude il buco esiste, scritta la stessa notte, in
#    `01-b8-cronometro.py:1571`: `gia = frase in testo_sano`.  Qui il confronto
#    lo fa `--giudica`, che vede i tre passi insieme (B0.4): questo script
#    raccoglie il fatto — «la marca c'era, si' o no» — per ciascun passo.
marca_vista() # $1 = sigla
{
	local ago
	ago=$(python3 "$FUORI/01-b12-guasti.py" --marca "$1" 2>/dev/null | tr -d '\r' | tail -1)
	if [ -z "$ago" ]; then
		# ⚠ Nessuna marca dichiarata: «non l'ho vista» sarebbe una risposta a
		#   una domanda che non e' stata posta.  Il rifiuto lo scrive
		#   `--giudica`, che sa che il campo e' vuoto.
		echo "false"
		return
	fi
	# ⛔ IL «--» NON E' PIGNOLERIA — rilievo R12-A.43, 11 agosto 2026.
	#    La marca di B2 e' «- credito uni DISPONIBILE a RCP all'apertura», e
	#    comincia con un trattino: senza `--`, `grep` la scambia per
	#    un'opzione, esce con errore, e questa funzione risponde «marca non
	#    vista».  ⇒ Il verdetto scriveva «il banco e' rosso ma la sua uscita
	#    non nomina la marca» su un'uscita che la nominava.
	# ⚠ E il sintomo e' indistinguibile da quello di una marca sbagliata: e'
	#   costato due giri di B2 prima di guardare qui invece che nel catalogo.
	if [ -f "$FUORI/b12-uscita.txt" ] && grep -qF -- "$ago" "$FUORI/b12-uscita.txt"; then
		echo "true"
	else
		echo "false"
	fi
}

# ⛔⭐ E OGNI RIGA DI ESITO PORTA LA SCENA — difetto D6, 12 agosto 2026.
#
# Questo file e' il verbale su cui `--giudica` scrive poi la riga di registro.
# ⛔ Senza il campo `scena`, due righe «B13 sano uscita 3» prodotte contro due
#    server diversi sono **indistinguibili**, e la prima cosa che si fa con un
#    verbale e' confrontarlo con un altro.  ⚠ E' la forma E8 applicata a un file
#    di esiti: «vuoto» e «un'altra scena» hanno lo stesso aspetto.
annota() # $1 = sigla, $2 = passo, $3 = uscita, $4 = marca_vista
{
	printf '{"sigla":"%s","passo":"%s","uscita":%s,"marca_vista":%s,"scena":"%s","bersaglio":"%s"}\n' \
		"$1" "$2" "$3" "$4" "$SCENA" "$BERSAGLIO" >> "$ESITI_FUORI"
}

# ⛔ E IL BANCO CHE NON SI E' POTUTO LANCIARE HA UNA RIGA SUA — R12-A.4.
#    Senza, finiva in `set(GUASTI) - set(per_sigla)`, cioe' fra i «mai
#    provati»: e «non ho una riga di comando per lanciarlo» e «nessuno l'ha mai
#    guardato» hanno due cure diverse.
annota_saltato() # $1 = sigla, $2 = perche'
{
	printf '{"sigla":"%s","passo":"saltato","uscita":9,"marca_vista":false,"scena":"%s","bersaglio":"%s","perche":"%s"}\n' \
		"$1" "$SCENA" "$BERSAGLIO" "$2" >> "$ESITI_FUORI"
}

# ---------------------------------------------------------------------------
log "Lo stato iniziale: la porta $PORTA"
chi_tiene_la_porta -ulnp
case $? in
0)	ko "la porta $PORTA e' gia' occupata:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "   Fermalo per PID (mai con pkill -f) e rilancia."
	exit 3 ;;
1)	ok "porta $PORTA libera (e «ss» ha parlato: non e' un silenzio)" ;;
*)	ko "⛔ non si e' potuto sapere chi tiene la porta $PORTA:"
	ko "   e «non si sa» non si arrotonda a «libera» — dodici certificazioni"
	ko "   poggerebbero su un server che potrebbe non essere il nostro"
	exit 3 ;;
esac

# ---------------------------------------------------------------------------
# ⛔⭐ LA SCALDATA DEL PRODOTTO — e non e' una comodita': senza, il passo 0/3
#     mentirebbe.  D6, 12 agosto 2026.
#
# `bsslserver` riceve i due certificati gia' fatti (li fa `01-b2-certificati.sh`);
# **`remotix` se li genera da se'**, dentro `--certificati`, alla prima
# accensione.  ⛔ E il passo 0/3 di B13 — `--verifica B13` — confronta le
# impronte di `pagina.pem` e `sessione.pem`: su una cartella vuota risponde
# *«non si leggono i due file»*, che e' **-1**, e il giro morirebbe dicendo che
# il guasto non e' innestabile.
#   ⚠ Cioe' un rosso che parla della cartella e non del banco — la forma che
#     questo file combatte da tre giorni.
# ⭐ Quindi si accende una volta, si aspetta che i due file esistano, e si
#    spegne: la scena si **prepara**, e la preparazione si dichiara.
if [ "$BERSAGLIO" = prodotto ]; then
	log "0-bis. ⭐ La scaldata: il prodotto si genera i propri certificati"
	if [ -f "$CERT_FUORI/sessione.pem" ] && [ -f "$CERT_FUORI/pagina.pem" ]; then
		ok "i due certificati ci sono gia' in $CERT: niente da scaldare"
		inf "sessione.pem $(md5sum "$CERT_FUORI/sessione.pem" | cut -c1-16)…"
		inf "pagina.pem   $(md5sum "$CERT_FUORI/pagina.pem"   | cut -c1-16)…"
	elif accendi sessione "scaldata"; then
		spegni
		if [ -f "$CERT_FUORI/sessione.pem" ] && [ -f "$CERT_FUORI/pagina.pem" ]; then
			ok "⭐ il prodotto ha scritto i suoi due certificati in $CERT"
		else
			ko "⛔ dopo la scaldata i due certificati NON ci sono in $CERT:"
			ko "   il passo 0/3 di B13 direbbe «non si leggono i due file», e"
			ko "   quel rosso parlerebbe della cartella, non del banco."
			exit 3
		fi
	else
		ko "⛔ la scaldata non e' riuscita: non misuro niente su una scena che"
		ko "   non si e' nemmeno accesa."
		exit 3
	fi
fi

for S in $SIGLE; do
	# ⛔ LA VERIFICA DELL'APPIGLIO VIENE PRIMA DEL GIRO SANO, E NON E' UN
	#    DETTAGLIO D'ORDINE.  Due ragioni, e la seconda l'ho pagata:
	#      · non ha senso spendere un giro sano per un guasto che non si
	#        potrebbe innestare;
	#      · ⛔ e' `--verifica` a costruire le COPIE dei banchi in
	#        `01-b12-copie/`.  Chiamandola dopo, il giro sano cercava un file
	#        che non esisteva ancora e usciva 2 — «python3: can't open file» —
	#        cioe' un rosso che non parlava ne' del banco ne' del guasto.
	log "=== $S — 0/3  lo stato di partenza che il guasto vuole"
	bash "$ENTRA" --root "python3 $GUASTI --verifica $S --certificati $CERT"
	COSTA=$(python3 "$FUORI/01-b12-guasti.py" --costa "$S" | tr -d '\r' | tail -1)
	# ⚠ Niente apostrofi dentro un `${…:-…}`: la shell li tratta come apici e
	#   il resto del file finisce dentro una stringa aperta.  E' la quinta
	#   veste della trappola delle shell annidate, gia' pagata in
	#   `01-b6-lancia.sh` su una riga d'errore che nessuno provava.
	inf "costa: ${COSTA:-NON LETTO}"

	log "=== $S — 1/3  il giro SANO (dev'essere verde)"
	gira "$S" sano; U=$?
	if [ "$U" -eq 9 ]; then
		inf "«$S» saltato: nessuna riga di comando — resta NON CERTIFICATO"
		annota_saltato "$S" "questo orchestratore non ha una riga di comando per lanciare il banco: catalogato e non eseguito"
		continue
	fi
	# ⛔ E LA MARCA SI GUARDA ANCHE QUI, invece di scrivere `false` a mano.
	#    Un `false` dichiarato senza guardare e' la stessa forma del rosso
	#    dichiarato senza misurare — e su B7 e' costato una certificazione
	#    finta (R12-A.3).
	M_SANO=$(marca_vista "$S")
	annota "$S" sano "$U" "$M_SANO"
	if [ "$M_SANO" = true ]; then
		ko "⛔ IL GIRO SANO DICE GIA' LA MARCA DI «$S»: qualunque cosa succeda"
		ko "   nel passo 2/3, vedere quella stringa nel rosso non provera'"
		ko "   niente.  Il verdetto lo scrivera' --giudica; il giro prosegue"
		ko "   perche' il resto delle misure vale lo stesso."
	fi

	log "=== $S — 2/3  si innesta il guasto"
	bash "$ENTRA" --root "python3 $GUASTI --applica $S --certificati $CERT"
	if [ $? -ne 0 ]; then
		ko "⛔ il guasto «$S» non si e' innestato: il passo non si fa"
		ko "   ⚠ e NON si annota un rosso: un guasto non innestato lascia il"
		ko "     banco verde, e chi legge concluderebbe l'opposto"
		continue
	fi
	SIGLA_APERTA=$S
	COSTA_APERTA=$COSTA
	if [ "$COSTA" = ricostruisce ]; then
		ricostruisci || { ko "⛔ senza binario non si misura niente"; ripulisci; continue; }
	fi
	gira "$S" guasto; U=$?
	annota "$S" guasto "$U" "$(marca_vista "$S")"

	log "=== $S — 3/3  si toglie il guasto e si torna al SANO"
	if ! ripulisci; then
		ko "⛔ il guasto «$S» non e' stato tolto (o il binario non e' stato"
		ko "   ricostruito): il terzo passo non vale, e ⛔ IL GIRO SI FERMA QUI."
		ko "   ⚠ Non e' prudenza: qualunque banco misurato dopo starebbe"
		ko "     guardando un codice che porta ancora il guasto di «$S», e il"
		ko "     suo rosso — o il suo verde — parlerebbe di un altro."
		break
	fi
	gira "$S" risano; U=$?
	annota "$S" risano "$U" "$(marca_vista "$S")"
done

# ---------------------------------------------------------------------------
log "Il verdetto — e lo da' chi vede i tre passi insieme (B0.4)"
# ⛔⭐ E LA SCENA GLIELA DICE CHI L'HA ACCESA — D6.  `--giudica` legge un file di
#     esiti e non ha nessun modo di sapere quale server li ha prodotti:
#     chiederglielo sarebbe chiedere a un verbale di ricordarsi la stanza.
#     ⚠ Senza `--scena` la riga di registro dice «non dichiarata», che e' quel
#       che e' — e non «innesto», che sarebbe una misura inventata.
bash "$ENTRA" --root "python3 $GUASTI --giudica $ESITI --scena \"$SCENA\""
E=$?
inf "gli esiti restano in $ESITI_FUORI"
exit "$E"
