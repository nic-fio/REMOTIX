#!/bin/bash
# ===========================================================================
# 11-gancio.sh — ⭐⭐ QUANDO PARTE LA RETE, E CHE COSA PARTE
# ===========================================================================
#
#   bash 11-gancio.sh decidi                 dice che cosa farebbe, e perche'
#   bash 11-gancio.sh gira [--secco]         decide e fa girare
#   bash 11-gancio.sh gira --famiglia rete           ⭐ costo quasi zero, davvero
#   bash 11-gancio.sh gira --famiglia rete-intera    ⛔ + C14: [M] ~800 s, e si
#                                                    prende le QUATTRO scatole
#   bash 11-gancio.sh gira --famiglia tutto --scatola gnome
#   bash 11-gancio.sh remoto [--secco]       ⭐ decide QUI, esegue LA', e riporta
#   bash 11-gancio.sh installa [pre-push|pre-commit] [--solo-qui]
#   bash 11-gancio.sh installato             c'e' o non c'e', e dove
#   bash 11-gancio.sh registro [n]           gli ultimi n giri
#
# ===========================================================================
# ⛔⛔ DEFINITO PER PERCORSO, NON PER BUONA VOLONTA' — `fasi/11…` §5.1
# ===========================================================================
#
# ⚠ La differenza non e' formale.  Un gancio che CHIEDE a chi lavora *«vuoi far
#   girare la rete?»* e' un gancio che, il giorno che si ha fretta, non gira —
#   ⛔ e i giorni in cui si ha fretta sono esattamente quelli in cui si rompono
#   le cose.
# ⇒ Qui la domanda non si fa: si guarda **quali file sono cambiati**, e da quelli
#   discende che cosa parte.  Chi lavora non ha una leva da tirare.
#
#   si tocca `src/` (il prodotto)      ⇒ la famiglia FUNZIONA
#   si toccano i banchi o la rete      ⇒ RETE: C10-C13, C15.  ⭐ Costo quasi
#                                        zero, e ⭐ nessuna accende una sessione
#   si tocca cio' da cui C14 dipende   ⇒ RETE-INTERA: la rete PIU' C14.
#     (`11-c14-*`, `11-c8-*`, `11-accendi.sh`, una `Contenitore.*`)
#     ⛔ `[M]` ~800 s, e si prende tutt'e quattro le scatole per tredici minuti
#   compare un `Contenitore.<nuovo>`   ⇒ desktop nuovo: tutto sul nuovo, PIU'
#                                        la regressione sui vecchi
#   si toccano solo i documenti        ⇒ ⭐ NIENTE, e si dice.  Un gancio che
#                                        gira anche quando non serve e' un
#                                        gancio che qualcuno spegnera'
#
# ⚠ E UNA COSA IL PERCORSO NON LA SA DIRE, dichiarata invece di essere nascosta:
#   *«prima di chiudere una fase»* non e' un file che cambia — e' una decisione.
#   ⇒ Quella si chiede per nome (`--famiglia tutto`), e va bene cosi': ⛔ far
#     finta che un percorso possa indovinarla vorrebbe dire una regola che non
#     scatta mai e che nessuno si accorge non essere scattata.
#
# ===========================================================================
# ⛔⛔ IL TETTO DEI 3 MINUTI, E LE PROVE CHE SONO STATE TAGLIATE
# ===========================================================================
#
# `fasi/11…` §5.1: sotto i 3 minuti per la famiglia veloce.  Sopra i 5 comincia
# il rischio che venga spenta; sopra i 10 e' quasi certo.  ⛔ E la regola su che
# cosa fare quando il tempo non ci sta: **si tagliano prove, non si alza il
# tetto.**
#
# `[M]` 26 agosto 2026 (`fasi/11…` §7-bis.13): **un giro di C1 costa 74
# secondi.**  ⇒ Nei 180 secondi ci stanno **DUE giri**, e basta.
#
# ⇒ ⭐⭐ QUEL CHE E' STATO TAGLIATO DALLA FAMIGLIA VELOCE, e quanto costa:
#
#   · **C1 dal terzo giro in poi** (otto giri su dieci).  ⛔ Costo: il documento
#     di fase dice che il guasto della nascita e' INTERMITTENTE, e con due giri
#     un guasto che colpisce una volta su cinque passa inosservato piu' della
#     meta' delle volte.  ⚠ Oggi non morde — `[M]` 26 ago 2026: dieci sessioni
#     su dieci nascono cieche, e due giri bastano ad accorgersene — ⛔ ma il
#     giorno in cui il difetto sara' curato e tornera' raro, DUE GIRI NON
#     BASTERANNO PIU', e questa riga e' li' per ricordarlo.
#   · **C8, tutt'e due le prove.**  ⛔ E' la maglia piu' importante della lista,
#     e questo taglio e' il piu' caro di tutti: il difetto del secondo inquilino
#     NON viene guardato a ogni modifica.  ⚠ Resta nella famiglia `tutto`, cioe'
#     prima di chiudere una fase.  ⇒ `[?]` Il costo vero: il primo avvio di
#     Firefox in una scatola fredda passa i 25 s (`LEZIONI.md` §1.45), e due
#     inquilini per quattro scatole non ci stanno in tre minuti in nessun modo.
#   · ⭐⭐ **LE CINQUE NUOVE DEL 27 AGOSTO — C2, C3, C4, C6, C8b.**  Nessuna
#     entra nella famiglia veloce, e non e' un rinvio: `[M]` il tetto e' pieno a
#     **173 s su 180**, e §5.1 dice che una maglia in piu' si SCAMBIA, non si
#     somma.  ⛔ Qui non c e niente da scambiare — la meno cara di queste costa
#     piu' dell intera famiglia veloce, perche' ognuna fa nascere una sessione.
#     ⇒ Stanno in `tutto` e in `desktop-nuovo`.
#     ⚠ E IL COSTO DEL TAGLIO, dichiarato: fra un invio e la chiusura di una
#     fase, **nessuno guarda se una finestra si apre, se i fotogrammi cambiano,
#     se un tasto arriva allo schermo, se un desktop si ritrova dopo un
#     distacco, e se la pagina si vede dal cliente**.  ⛔ Sono cinque delle sei
#     domande che l utente si fa guardando lo schermo.  ⇒ La cura non e'
#     alzare il tetto: e' che una sessione costi meno a nascere.
#   · **il passo 0.**  Guarda l'AMBIENTE, che non cambia quando cambia `src/`.
#     ⚠ Costo basso e dichiarato: se qualcuno ricostruisce una scatola senza
#     dirlo, la famiglia veloce non se ne accorge.  ⭐ Ma se ne accorge **C11**,
#     che nella famiglia veloce c'e' — ed e' per questo che c'e'.
#
# ⛔ E il tetto NON e' creduto: ogni giro si CRONOMETRA e il tempo finisce nel
#    registro.  Se sfora, il gancio lo dice a voce alta invece di tirare avanti.
#    ⇒ Il `[?]` dei tre minuti diventera' un `[M]` al primo giro vero.
#
# ===========================================================================
# ⭐⭐ E LASCIA TRACCIA — perche' senza traccia C12 e C13 non esistono
# ===========================================================================
#
# Un giro per riga, in `11-gancio-registro.jsonl`, in coda e mai riscritto.
# ⛔ E fra i campi ce n'e' uno che vale piu' degli altri: **`secco`**.
#
# ⚠ Un giro a vuoto (`--secco`) NON e' un giro.  Se contasse, basterebbe un
#   `--secco` a far dire a C12 *«il gancio e' vivo»* per una settimana, ⛔ cioe'
#   la rete si racconterebbe che sta girando mentre non gira.  ⇒ La riga si
#   scrive lo stesso (serve a chi diagnostica), ma porta `"secco": true`, e
#   **C12 e C13 la buttano via**.  ⭐ E tutt'e due hanno quel caso dentro la
#   loro certificazione, cioe' e' provato e non promesso.
#
# ⛔ NIENTE `sh -c` annidati qui dentro: `LEZIONI.md` §1.46 — un comando che
#    perde le virgolette non esegue niente e restituisce 0, cioe' un banco che
#    non ha girato e dice «riuscito».  Ogni maglia si chiama con un ARRAY.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(git -C "$QUI" rev-parse --show-toplevel 2>/dev/null)
REGISTRO="$QUI/11-gancio-registro.jsonl"

# ⚠ Ogni riga di registro dice SU QUALE MACCHINA e' stata scritta.  ⛔ Non e' un
#   ornamento: da quando i giri di due macchine finiscono nello stesso file
#   (`11-registro-unisci.py`), una riga senza questo campo e' una riga di cui non
#   si sa piu' se ha visto delle scatole o soltanto un deposito git.
DOVE=$(hostname 2>/dev/null) || DOVE=""
[ -n "$DOVE" ] || DOVE=sconosciuta

# ---------------------------------------------------------------------------
# ⭐⭐ LA MACCHINA DI PROVA — dove il gancio ESEGUE.  `DECISIONI.md`
#    §4.6-novemdecies: decidere vuole il deposito, far girare vuole le scatole.
# ---------------------------------------------------------------------------
RETE11_REMOTA=/media/REMOTIX/rete11
# ⚠ Il nome dell'unita' si puo' cambiare (`--unita`) per una ragione sola: due
#   giri insieme sulla stessa macchina si pesterebbero l'unita' e il log.
#   ⛔ Non e' una leva per far girare meno cose — quelle non ci sono.
UNITA_REMOTA=rete11-gancio
# ⛔ Il tetto d'attesa della meta' remota.  ⚠ NON e' il tetto dei 3 minuti: e'
#   quanto si sta ad aspettare prima di dire «non ho potuto guardare».  La
#   famiglia `tutto` costa `[M]` 1 704 s (§7-bis.16), quindi non puo' essere 180.
ATTESA_REMOTA=2400

# ⛔ Il tetto sta QUI, dichiarato, e si stampa in ogni giro: un verdetto senza
#    il suo metro e' un'opinione.
TETTO_VELOCE=180

# ⚠ Quanto ci si aspetta che costi ciascuna maglia.  Serve a UNA cosa sola: non
#   iniziare una maglia che non ci sta nel tempo rimasto.  ⛔ E' una previsione,
#   non una misura — solo C1 ha un `[M]` sotto:
#     C1   `[M]` 74 s a giro, 26 ago 2026, `fasi/11…` §7-bis.13
#     C11  `[?]` interroga quattro scatole con dpkg, secondi
#     C12  `[?]` legge due file
#     C13  `[?]` legge un file
#     C14  ⛔ `[M]` **786 s** — §7-bis.16, giro completo del 26 ago 2026. E
#          ⛔ accende tutt'e quattro le scatole INSIEME: non e' una maglia a
#          costo quasi zero, e per questo NON sta piu' nella famiglia `rete`
#     C15  `[?]` legge un file, come C12 e C13
#     C5   `[M]` 71 s a giro — 27 ago 2026, dopo la cura dei tetti morti
#          (`--attesa-sink` 26 s + `--resta` 51 s).  ⛔ Prima diceva 45, che era
#          la misura di PRIMA della cura: un costo vecchio fa saltare una maglia
#          che ci starebbe, o ne fa partire una che non ci sta
#   ⭐⭐ LE CINQUE MAGLIE NUOVE del 27 agosto 2026 — i costi stanno accanto
#   alla loro dichiarazione qui sotto, con la marca vera di ciascuno.
#     C7   `[M]` 26 s il giro normale, 25 s «si stacca soltanto», 37 s col
#          guasto innestato (26 ago 2026, scatola XFCE) — dichiarato 30
#     C9   `[M]` 50 s (--resta 45), 26 ago 2026, scatola lxqt
#     C10  ⭐ `[M]` **0,039 s** — legge tre file e una riga del Makefile.
#          26 ago 2026, mediana su dieci giri sul portatile
COSTO_C1_GIRO=74
# ⛔ 27 ago 2026: era **45**, cioe' la misura di PRIMA che C5 fosse curata dei
#    suoi tetti morti.  ⚠ Un costo che resta indietro non e' innocuo: governa se
#    una maglia si comincia o si salta.
COSTO_C5=71
COSTO_C7=30
COSTO_C9=50
COSTO_C10=1
COSTO_C11=20
COSTO_C12=5
COSTO_C13=5
COSTO_C14=800
COSTO_C15=5

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LE CINQUE MAGLIE NUOVE — 27 agosto 2026.  ⛔ NESSUNA sta nella famiglia
#    veloce, e non e' una svista: `[M]` il tetto e' pieno a 173 s su 180, e
#    §5.1 dice che una maglia in piu' si SCAMBIA, non si somma.  Qui non c e
#    niente da scambiare: la meno cara di queste costa piu' dell intera
#    famiglia veloce.  ⇒ Stanno in `tutto` e in `desktop-nuovo`.
# ⚠ E girano SOLO su gnome: `[R]` il prodotto sa avviare solo GNOME
#   (`src/sessione.c:778`, tutto `src/mutter.c`).  Sulle altre tre danno 3.
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ `[M]` 27 agosto 2026, scatola rete11-gnome curata, giro normale cronometrato
#   dal sistema.  ⚠ Col guasto innestato C2 apre DUE inquilini e costa il doppio
#   (`[M]` 418 e 419 s); C3 col codificatore fermo costa `[M]` 321 s.
COSTO_C2=210
COSTO_C3=162
COSTO_C4=32
COSTO_C6=205
COSTO_C8B=378

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL TETTO DEL PALCO DI C2 E C3 — ⛔ un numero, in un posto solo.
#
# `[M]` 27 agosto 2026, scatola gnome curata: il palco nasce in **2,1 · 2,2 ·
# 2,3 · 4,1 · 4,2 secondi** (cinque giri) — massimo **4,2 s**.  ⛔ Il valore
# predefinito dentro le due maglie e' ancora **200 s**, che veniva dai ~97 s di
# quando nella scatola il `polkit` non partiva.
#
# ⛔⛔ E in C2 e C3 quel numero NON e' una scadenza: e' un ADDENDO.  Le due
#     maglie calcolano `--resta = attesa-palco + ... `, cioe' quanto il cliente
#     resta attaccato: con 200 il cliente sta attaccato 255 s **anche quando il
#     palco e' nato dopo 2 secondi**.  ⇒ 140 secondi buttati a ogni inquilino.
# ⚠ In C4 e in C6 invece e' una scadenza vera (si aspetta FINCHE' nasce), e
#   percio' qui non si passa: allungarlo o accorciarlo non cambia il costo, e
#   un tetto passato da fuori senza ragione e' rumore.
#
# ⇒ **60 s = 14 volte il massimo misurato.**  ⛔ E il posto giusto per questo
#   numero e' il `default` delle due maglie: qui sta perche' il 27 agosto le
#   maglie erano in mano a un altro agente e non si toccano in due.
#   ⚠ Il giorno che il default scende, questa riga va TOLTA, non lasciata.
# ═══════════════════════════════════════════════════════════════════════════
TETTO_PALCO_C2C3=60

GIRI_VELOCE=2

DESKTOP_NOTI="gnome kde xfce lxqt"

# ---------------------------------------------------------------------------
# ⛔⛔ DOVE STANNO I GANCI DI GIT — e non e' una riga sola, per una ragione.
#
# `git --git-path` torna un percorso **relativo alla cartella data a `-C`**, non
# alla radice del deposito.  `[M]` 26 agosto 2026: chiamato da `banchi/11-scatole`
# risponde `../../.git/hooks`.  ⇒ Usarlo cosi com e vuol dire un percorso che
# dipende da dove ci si trovava quando si e chiamato — cioe un gancio che a
# volte si installa nel posto giusto e a volte no, senza dirlo.
# ⚠ E lo stesso identico difetto ha morso C12, che diceva «non installato» per
#   sempre.  ⇒ La risoluzione sta QUI, in un posto solo.
# ---------------------------------------------------------------------------
cartella_ganci() {
	local c
	c=$(git -C "$RADICE" rev-parse --git-path hooks 2>/dev/null) || return 1
	case "$c" in
	/*) printf '%s' "$c" ;;
	*)  printf '%s/%s' "$RADICE" "$c" ;;
	esac
}

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '      %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⚠ L'unica scrittura JSON di questo file, e sta in un posto solo apposta: un
#   secondo punto che costruisce JSON e' un secondo punto che puo' costruirlo
#   storto senza che nessuno se ne accorga.
# ---------------------------------------------------------------------------
json_stringa() {
	local s=${1-}
	s=${s//\\/\\\\}
	s=${s//\"/\\\"}
	s=${s//$'\n'/ }
	s=${s//$'\t'/ }
	printf '"%s"' "$s"
}

json_elenco() {
	local primo=1 v
	printf '['
	for v in "$@"; do
		[ $primo -eq 1 ] || printf ','
		primo=0
		json_stringa "$v"
	done
	printf ']'
}

# ---------------------------------------------------------------------------
# ⭐ CHE COSA E' CAMBIATO — e da dove lo si guarda
#
# ⚠ Il confronto NON e' lo stesso per tutti gli inneschi, e dev'essere quello
#   giusto o il gancio guarda il posto sbagliato:
#     pre-commit   quel che sta per entrare nel commit  (`--cached`)
#     pre-push     quel che sta per partire             (`@{upstream}..HEAD`)
#     a mano       quel che c'e' adesso sotto le mani   (albero + staged)
# ---------------------------------------------------------------------------
cambiati() {
	local innesco=$1
	# ⛔ Senza deposito non c e niente da elencare, e NON e un errore: e la
	#    macchina di prova, dove il gancio ESEGUE invece di DECIDERE.
	#    ⚠ Senza questa riga uscivano tre `git: command not found` su ogni giro,
	#      cioe rumore che somiglia a un guasto.
	[ -n "$RADICE" ] || return 0
	case "$innesco" in
	pre-commit)
		git -C "$RADICE" diff --name-only --cached
		;;
	pre-push)
		# ⚠ Se non c'e' un ramo a monte (ramo nuovo), non si puo' fare la
		#   differenza: si guarda l'ultimo commit.  ⛔ E si preferisce
		#   guardare TROPPO piuttosto che troppo poco — un gancio che salta
		#   e' peggio di un gancio che gira di piu'.
		local monte
		monte=$(git -C "$RADICE" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null)
		if [ -n "$monte" ]; then
			git -C "$RADICE" diff --name-only "$monte..HEAD"
		else
			git -C "$RADICE" show --name-only --pretty=format: HEAD
		fi
		;;
	*)
		git -C "$RADICE" diff --name-only HEAD
		git -C "$RADICE" diff --name-only --cached
		git -C "$RADICE" ls-files --others --exclude-standard
		;;
	esac | sed '/^$/d' | sort -u
}

# ---------------------------------------------------------------------------
# ⭐⭐ LA REGOLA, tutta qui: dai percorsi alla famiglia.
#
# ⛔ E l'ordine conta: «desktop nuovo» vince su tutto, perche' e' il caso in cui
#    la regressione sui vecchi serve di piu' — ed e' anche l'unico in cui il
#    percorso sa dire una cosa che nessuno pensava di dichiarare.
# ---------------------------------------------------------------------------
decidi_famiglia() {
	local -n _elenco=$1
	local f tocca_prodotto=0 tocca_rete=0 nuovo=""

	# Un desktop nuovo si riconosce da una ricetta AGGIUNTA, non modificata.
	local aggiunti
	aggiunti=$(git -C "$RADICE" diff --name-only --diff-filter=A --cached 2>/dev/null
	           git -C "$RADICE" ls-files --others --exclude-standard 2>/dev/null)
	for f in $aggiunti; do
		case "$f" in
		banchi/11-scatole/Contenitore.*)
			local nome=${f##*Contenitore.}
			case " $DESKTOP_NOTI " in
			*" $nome "*) : ;;
			*) nuovo="$nome" ;;
			esac
			;;
		esac
	done

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐ E I QUATTRO PERCORSI DA CUI C14 DIPENDE — dichiarati, non intuiti.
	#
	# ⛔ C14 non sta piu' nella famiglia `rete` (costa `[M]` 786 s e si prende
	#    le quattro scatole: vedi `famiglia_rete`).  ⚠ Ma toglierla e basta
	#    vorrebbe dire che un cambiamento **a C14 stessa** non la fa piu'
	#    girare — cioe' §5.2, *«una prova che non prende niente si toglie»*,
	#    ottenuto per disuso invece che per decisione.
	# ⇒ ⭐ Quindi non si toglie: si SPOSTA su un percorso suo.  E il percorso
	#   non e' arbitrario — sono le quattro cose che, cambiando, cambiano
	#   proprio quel che C14 misura:
	#
	#   `11-accendi.sh`      ⭐ ci sta dentro la MAPPA DELLE PORTE (righe 58-62,
	#                        gnome 8511 · kde 8512 · xfce 8513 · lxqt 8514), ed
	#                        e' li' che e' scritto il prezzo di `--network=host`.
	#                        ⛔ C14 quelle porte **le ricopia** — e un numero
	#                        ricopiato che cambia da una parte sola e' esattamente
	#                        il difetto che C14 esiste per prendere
	#   `Contenitore.*`      la ricetta della scatola: se cambia come nasce, cambia
	#                        se due possono stare accese insieme
	#   `11-c8-*`            ⭐ e' la SONDA di C14 (usa la prova A di C8): se cambia
	#                        la sonda, cambia l'impronta che C14 confronta
	#   `11-c14-*`           la maglia stessa
	# ═══════════════════════════════════════════════════════════════════
	local tocca_c14=0
	for f in "${_elenco[@]}"; do
		case "$f" in
		src/*|web/*)          tocca_prodotto=1 ;;
		esac
		case "$f" in
		*/11-accendi.sh|*/Contenitore.*|*/11-c8-*|*/11-c14-*) tocca_c14=1 ;;
		esac
		case "$f" in
		banchi/*)             tocca_rete=1 ;;
		esac
	done

	if [ -n "$nuovo" ]; then
		printf 'desktop-nuovo:%s' "$nuovo"
	elif [ $tocca_prodotto -eq 1 ]; then
		printf 'funziona'
	elif [ $tocca_c14 -eq 1 ]; then
		printf 'rete-intera'
	elif [ $tocca_rete -eq 1 ]; then
		printf 'rete'
	else
		printf 'niente'
	fi
}

perche_famiglia() {
	case "${1%%:*}" in
	desktop-nuovo) printf 'e comparsa la ricetta di un desktop che non c era: %s' "${1##*:}" ;;
	funziona)      printf 'e cambiato il PRODOTTO (src/ o web/)' ;;
	rete-intera)   printf 'e cambiato qualcosa da cui C14 dipende (accendi, una ricetta, C8, C14) ⇒ ⛔ ~800 s e le quattro scatole' ;;
	rete)          printf 'sono cambiati i banchi o la rete (banchi/)' ;;
	niente)        printf 'non e cambiato niente che la rete guardi' ;;
	esac
}

# ---------------------------------------------------------------------------
# ⭐ FAR GIRARE UNA MAGLIA, cronometrandola — e senza gusci in mezzo.
#
# Riempie tre variabili globali, e non torna una stringa da spezzare: ⛔ una
# stringa da spezzare e' un posto dove un esito puo' perdersi in silenzio.
# ---------------------------------------------------------------------------
M_ESITO=0
M_SECONDI=0
# ⭐ l esito di C10, tenuto da parte: decide se ha senso innestarle un guasto.
ESITO_C10=3
eseguiti_json=""

esegui_maglia() {
	local nome=$1 guasto=$2; shift 2
	local prima dopo

	if [ "$SECCO" = 1 ]; then
		inf "(a vuoto) $nome  ⇒  $*"
		M_ESITO=-1
		M_SECONDI=0
	else
		prima=$SECONDS
		"$@"
		M_ESITO=$?
		dopo=$SECONDS
		M_SECONDI=$((dopo - prima))
		case "$M_ESITO" in
		0) ok  "$nome — regge  (${M_SECONDI}s)" ;;
		1) ko  "$nome — NON REGGE  (${M_SECONDI}s)" ;;
		3) inf "?   $nome — non ho potuto guardare  (${M_SECONDI}s)" ;;
		4) inf "?   $nome — il turno non e mai arrivato  (${M_SECONDI}s)" ;;
		*) inf "?   $nome — esito $M_ESITO  (${M_SECONDI}s)" ;;
		esac
	fi

	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ E QUI STA UNA COSA CHE, SE SI PERDE, RENDE C13 UNA BUGIA.
	#
	# Una maglia col GUASTO INNESTATO si legge **AL CONTRARIO**: `C8 --senza-cura`
	# esce **0** quando il guasto E' STATO VISTO, e **1** quando NON lo e' stato.
	# ⇒ Cioe' su un giro innestato lo `0` e' la buona notizia.
	#
	# ⚠ Se questa inversione restasse implicita, C13 andrebbe a cercare «un giro
	#   con un guasto innestato e un rosso», ⛔ e la troverebbe anche quando il
	#   rosso viene da UN'ALTRA maglia — per esempio da C1, che il guasto vero ce
	#   l ha davvero.  ⇒ C13 direbbe «la rete sa dare rosso» avendo guardato una
	#   maglia che non c entra niente.
	#
	# ⭐ Percio' l inversione sta QUI, in un posto solo, e nel registro finisce il
	#   fatto invece dell esito grezzo: **`ha_visto_il_guasto`**.  C13 legge
	#   quello e non ha bisogno di sapere niente di come esce C8.
	# ═══════════════════════════════════════════════════════════════════
	local visto=""
	# ⚠ A vuoto non si e' visto niente, ne' in un senso ne' nell altro: la
	#   chiave non si scrive affatto.  ⛔ Scriverla `false` direbbe «il guasto
	#   non e' stato visto», che e' un'accusa a una prova che non e' girata.
	#
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔⛔ E LA STESSA ACCUSA LA FACEVA L'ESITO **3**, per tutte le maglie
	#      tranne C10.  27 agosto 2026, rilievo di un agente mandato a refutare.
	#
	# Qui c'era `if esito = 0 … else false`: ⇒ un `3` — «non ho potuto
	# guardare» — finiva scritto **`ha_visto_il_guasto: false`**, cioe' *«il
	# guasto le e' passato sotto il naso e non l'ha visto»*.
	# ⛔ Ma una maglia che non ha guardato non ha ne' visto ne' mancato: e'
	#    esattamente il caso di `--secco` qui sopra, e li' la regola c'era gia'.
	# ⇒ Il giorno che su una scatola le innestate uscissero tutte 3 (server
	#   fermo, scatola non accesa, prodotto non ancora dentro), ⛔ **C13
	#   comincerebbe a gridare «la rete non sa piu' dare rosso» mentre la rete
	#   sta benissimo** — il difetto che C13 esiste per prendere, prodotto dal
	#   gancio stesso.
	#
	# ⛔⛔ E NON BASTA OMETTERE LA CHIAVE, che era la cura ovvia: **C13 conta le
	#     maglie per `guasto_innestato`**, e per lei una chiave ASSENTE vale
	#     «non visto» (`11-c13…`, ha quel caso dentro la certificazione: *«e del
	#     suo esito non si sa niente ⇒ ROSSO»*, ed e' giusto cosi').
	# ⇒ Quindi cade anche `guasto_innestato`: se la maglia non ha giudicato,
	#   **in questo giro non e' stata certificata**, e la riga lo dice.  ⭐ E' la
	#   stessa forma che `salta_maglia` usa da sempre — `guasto_innestato:false`
	#   piu' la RAGIONE — invece di due modi diversi di dire la stessa cosa.
	# ⚠ E il fatto non si perde: resta `innesto_non_giudicato`, per chi diagnostica.
	# ═══════════════════════════════════════════════════════════════════
	local guasto_scritto=$guasto
	if [ "$guasto" = true ] && [ "$SECCO" != 1 ]; then
		case "$M_ESITO" in
		0)
			visto=',"ha_visto_il_guasto":true'
			ok "  ⭐ il guasto innestato E' STATO VISTO — la rete sa ancora dare rosso"
			;;
		1)
			visto=',"ha_visto_il_guasto":false'
			ko "  ⛔⛔ il guasto innestato NON e' stato visto (esito $M_ESITO)"
			;;
		*)
			# ⛔ Ne' `true` ne' `false`: non ha guardato.  ⚠ E si dice a voce —
			#   «non ho potuto innestare il guasto» e' un'informazione, non un
			#   silenzio, e un 3 che si ripete e' un guasto del banco (§5.2).
			guasto_scritto=false
			visto=',"innesto_non_giudicato":true'
			inf "  ⚠ il guasto era innestato e la maglia NON HA POTUTO GUARDARE (esito $M_ESITO)"
			inf "    ⇒ questo giro NON la certifica, e ⛔ nemmeno la accusa:"
			inf "      per C13 e' come se il guasto non fosse stato innestato"
			;;
		esac
	fi

	[ -n "$eseguiti_json" ] && eseguiti_json="$eseguiti_json,"
	eseguiti_json="$eseguiti_json{\"nome\":$(json_stringa "$nome"),\"esito\":$M_ESITO,\"secondi\":$M_SECONDI,\"guasto_innestato\":$guasto_scritto$visto}"
}

salta_maglia() {
	local nome=$1 perche=$2
	inf "⚠ SALTATA $nome — $perche"
	[ -n "$eseguiti_json" ] && eseguiti_json="$eseguiti_json,"
	eseguiti_json="$eseguiti_json{\"nome\":$(json_stringa "$nome"),\"esito\":3,\"secondi\":0,\"guasto_innestato\":false,\"saltata\":$(json_stringa "$perche")}"
}

# ---------------------------------------------------------------------------
# ⛔⛔ LE MAGLIE SI CERCANO PER PREFISSO, non per nome intero.
#
# ⚠ Una maglia che non c'e' NON e' un verde e NON e' un rosso: e' «non ho potuto
#   guardare».  ⛔ Darla per buona perche' il file manca sarebbe la forma
#   d errore che questa fase esiste per non ripetere.
#
# ⭐ E il prefisso non e' pigrizia: `[M]` 26 agosto 2026, la prima stesura
#   inchiodava `11-c14-le-scatole-non-si-disturbano.py`, e il file vero si
#   chiama `11-c14-non-si-disturbano.py`.  ⇒ Il gancio avrebbe detto «SALTATA
#   C14 — il file non c e» per sempre, ⛔ e avrebbe avuto ragione da un punto di
#   vista sbagliato: la maglia c era, ero io a chiamarla col nome storto.
# ⚠ E se ce ne fossero DUE con lo stesso numero non si tira a indovinare: si
#   dice, perche' scegliere in silenzio vorrebbe dire far girare una maglia e
#   crederne un altra.
# ---------------------------------------------------------------------------
QUALE_MAGLIA=""
trova_maglia() {
	local numero=$1 trovati
	QUALE_MAGLIA=""
	trovati=$(ls "$QUI"/11-"$numero"-*.py 2>/dev/null)
	case $(printf '%s\n' "$trovati" | sed '/^$/d' | wc -l) in
	0) return 1 ;;
	1) QUALE_MAGLIA=$trovati; return 0 ;;
	*) QUALE_MAGLIA="TROPPE"; return 1 ;;
	esac
}

# ---------------------------------------------------------------------------
GIRA_MAGLIA() { python3 "$1"; }
GIRA_C1()  { bash "$QUI/11-accendi.sh" c1 "$1" "$2"; }
GIRA_C2()  { bash "$QUI/11-accendi.sh" c2 "$1" "${@:2}"; }
GIRA_C3()  { bash "$QUI/11-accendi.sh" c3 "$1" "${@:2}"; }
GIRA_C4()  { bash "$QUI/11-accendi.sh" c4 "$1" "${@:2}"; }
GIRA_C6()  { bash "$QUI/11-accendi.sh" c6 "$1" "${@:2}"; }
GIRA_C8()  { bash "$QUI/11-accendi.sh" c8 "$1" "${@:2}"; }
GIRA_C8B() { bash "$QUI/11-accendi.sh" c8b "$1" "${@:2}"; }
GIRA_C5()  { bash "$QUI/11-accendi.sh" c5 "$1" "${@:2}"; }
GIRA_C7()  { bash "$QUI/11-accendi.sh" c7 "$1" "${@:2}"; }
GIRA_C9()  { bash "$QUI/11-accendi.sh" c9 "$1" "${@:2}"; }
# ⭐ C10 col guasto innestato: gira SUL DEPOSITO, non su una scatola — ⇒ e' la
#   sola maglia con un guasto innestato che la meta'-portatile del gancio possa
#   far girare.  ⛔ Senza, C13 su quella meta' non potrebbe mai diventare verde.
GIRA_C10G() { python3 "$1" --guasto-innestato; }
GIRA_P0()  { bash "$QUI/11-accendi.sh" passo0 "$1"; }

# ---------------------------------------------------------------------------
# LE FAMIGLIE
# ---------------------------------------------------------------------------
famiglia_rete() {
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ QUI C'ERA DENTRO C14, E LA RIGA ACCANTO PROMETTEVA «costo quasi zero,
	#     e nessuna accende una sessione (§4.2)».  ⛔ **Era falso, e di molto.**
	#
	# `[M]` §7-bis.16, giro completo del 26 agosto 2026: **C14 costa 786 s**, e
	# per misurare che le scatole non si disturbano le accende **tutt'e quattro
	# insieme** e ci fa girare dentro la prova A di C8.
	# ⇒ ⚠ Chi leggeva quella riga credeva di poter lanciare `--famiglia rete`
	#   accanto a un'altra misura senza disturbarla: ⛔ e invece si prendeva le
	#   quattro scatole per tredici minuti.  ⛔ E' la trappola di `LEZIONI.md`
	#   §1.50 — un commento che descrive una grandezza diversa da quella che il
	#   codice governa — con l'aggravante che qui il numero e' 786 contro «zero».
	#
	# ⭐⭐ E LA CURA SCELTA E' **DIVIDERE**, non riscrivere il commento.  Perche':
	#
	#   · ⛔ **dichiarare e basta non bastava.**  Il costo vero era gia' scritto
	#     in un commento, e la famiglia costava lo stesso 786 s: un cartello non
	#     e' una cura.  E questa famiglia scatta su OGNI cambiamento a `banchi/`,
	#     cioe' — in questa fase — su quasi ogni invio.  ⇒ Tredici minuti a ogni
	#     invio sono esattamente la cosa che §5.1 dice che fa **spegnere** un
	#     gancio.
	#   · ⛔ **spostarla in `tutto` e basta l'avrebbe fatta marcire.**  Un
	#     cambiamento a C14 stessa non l'avrebbe piu' fatta girare: §5.2 dice
	#     che *«una prova che non prende niente si toglie, e si scrive perche'»*
	#     ⛔ — non che si lascia morire per disuso.
	#   · ⭐ **Dividere le tiene tutt'e due**: `rete` torna a essere quel che
	#     §4.2 prometteva, e C14 resta agganciata **al percorso da cui dipende**
	#     (`decidi_famiglia`, dove c'e' scritto quali e perche'), piu' che a
	#     `tutto`, a `desktop-nuovo`, e al nome `--famiglia rete-intera`.
	#
	# ⭐ IL COSTO DI QUESTA FAMIGLIA, adesso vero: **sul portatile** `[M]` circa
	#   1 s (C11 non trova le scatole e dice «non ho potuto guardare»);
	#   **sulla macchina di prova** `[M]` ~11 s, che e' C11 — e nessuna accende
	#   una sessione.  ⇒ Il patto di §4.2 e' rispettato invece che ereditato.
	#
	# ⛔ IL PREZZO, dichiarato: un cambiamento a `banchi/` che NON tocca i
	#    quattro percorsi di C14 non fa piu' girare C14.  ⚠ Se un giorno si
	#    scoprisse che C14 dipende da qualcos'altro, la cura e' **aggiungere quel
	#    percorso** li' sopra, ⛔ non rimetterla qui dentro.
	# ═══════════════════════════════════════════════════════════════════
	local n
	# ⚠ C10 e' una maglia del PRODOTTO (§4.1), non della rete — sta qui perche la
	#   meta' gemella vive in `banchi/rcp/`: un cambiamento li' fa scattare QUESTA
	#   famiglia, ed e' ⛔ esattamente il cambiamento che rompe il gemello.
	#   ⭐ E rispetta il patto di §4.2: costo quasi zero, e non accende niente.
	# ⭐ C15 guarda se la META' REMOTA gira davvero: legge il registro, costa
	#   quanto C12 e C13, ⛔ e sulla macchina di prova esce **2** apposta (li' il
	#   registro non e' la memoria unita, e sarebbe verde qualunque cosa succeda).
	for n in c10 c11 c12 c13 c15; do
		local N=${n^^}
		if trova_maglia "$n"; then
			esegui_maglia "$N" false GIRA_MAGLIA "$QUALE_MAGLIA"
			# ⭐ si tiene da parte l esito di C10: serve fra poco per decidere
			#   se ha senso innestarle un guasto.
			[ "$n" = c10 ] && ESITO_C10=$M_ESITO
		elif [ "$QUALE_MAGLIA" = TROPPE ]; then
			salta_maglia "$N" "ce ne sono PIU DI UNA con questo numero: non tiro a indovinare"
		else
			salta_maglia "$N" "il file non c e"
		fi
	done
	# ⭐⭐ E IL GUASTO INNESTATO, §3.6.  ⛔ Non e' un lusso: e' l unica riga di
	#    questa famiglia che tiene in vita C13 quando il gancio gira sul
	#    portatile, dove le scatole non ci sono.  Costa `[M]` 0,1 s.
	# ⛔ E anche qui: solo se C10 ha potuto guardare — vedi `famiglia_veloce`.
	if trova_maglia c10; then
		if [ "${ESITO_C10:-3}" = 0 ] || [ "${ESITO_C10:-3}" = 1 ]; then
			esegui_maglia "C10 guasto innestato" true GIRA_C10G "$QUALE_MAGLIA"
		else
			salta_maglia "C10 guasto innestato" "C10 non ha potuto guardare: qui non c e il deposito"
		fi
	fi
}

# ---------------------------------------------------------------------------
# ⭐⭐ LA RETE **PIU' C14** — e il costo si dice PRIMA di cominciare.
#
# ⛔ Dirlo dopo non servirebbe a niente: chi si accorge di aver lanciato la cosa
#    sbagliata deve poterla fermare, non leggerne il conto a tredici minuti di
#    distanza.  ⚠ E' la stessa ragione per cui il tetto si rispetta prima di
#    cominciare una maglia invece di troncarla a meta' (§5.1).
# ---------------------------------------------------------------------------
famiglia_rete_intera() {
	famiglia_rete
	log "e adesso C14 — ⛔ [M] 786 s (§7-bis.16), e SI PRENDE LE QUATTRO SCATOLE"
	inf "⛔ se in questo momento qualcuno sta misurando su rete11-*, questo giro"
	inf "  gliele porta via: §3.4, una scatola per volta per il lucchetto della"
	inf "  scheda.  ⇒ Si ferma con Ctrl-C adesso, non fra tredici minuti."
	inf "⚠ e per la rete SENZA C14: --famiglia rete  ([M] ~11 s, non accende niente)"
	if trova_maglia c14; then
		esegui_maglia C14 false GIRA_MAGLIA "$QUALE_MAGLIA"
	elif [ "$QUALE_MAGLIA" = TROPPE ]; then
		salta_maglia C14 "ce ne sono PIU DI UNA con questo numero: non tiro a indovinare"
	else
		salta_maglia C14 "il file non c e"
	fi
}

famiglia_veloce() {
	# ⛔ Il tetto si RISPETTA prima di cominciare una maglia, non si tronca a
	#    meta': troncare darebbe un rosso che non e' del prodotto — la forma
	#    d errore di `LEZIONI.md` §1.45.
	local speso rimasto
	# ⭐⭐ C10 PER PRIMA, e per due ragioni: gira **prima di compilare** (e' il
	#    momento in cui il difetto si ferma a costo zero), e ⛔ costa meno della
	#    risoluzione di questo cronometro, che conta in secondi interi.
	#    `[M]` 26 ago 2026: 0,039 s mediana su dieci giri.
	# ⚠ §5.1 dice che il tetto e' pieno (153 s su 180) e che una maglia in piu' va
	#   SCAMBIATA, non sommata.  ⭐ Qui non c e niente da scambiare: 0,04 s non
	#   muovono un numero contato in secondi interi — e il tetto resta 153 s.
	if trova_maglia c10; then
		esegui_maglia C10 false GIRA_MAGLIA "$QUALE_MAGLIA"
		# ⭐ e il suo guasto innestato, che costa `[M]` 0,1 s: e' quel che
		#   permette a C13 di dire «la rete sa ancora dare rosso» anche in un
		#   giro veloce, senza accendere niente.
		# ⛔⛔ MA SOLO SE C10 HA POTUTO GUARDARE.  Sulla macchina di prova il
		#    deposito non c e (§4.6-novemdecies): C10 direbbe «non lo so», il
		#    guasto innestato pure.
		#    ⇒ Se non ha potuto guardare non si innesta niente: non c e ragione
		#      di far girare una prova che non puo' giudicare.
		# ⚠ 27 agosto 2026 — QUESTA GUARDIA NON E' PIU' L'UNICA DIFESA, ed e'
		#   giusto dirlo perche' prima lo era: senza, `esegui_maglia` scriveva
		#   `ha_visto_il_guasto: false` su un esito 3, cioe' un'accusa alla rete
		#   per un guasto che nessuno aveva giudicato.  ⭐ Adesso quella regola
		#   sta DENTRO `esegui_maglia` e vale per TUTTE le maglie, non per C10
		#   soltanto.  ⇒ Qui resta perche' fa due cose in piu': non spreca il
		#   giro, e scrive una ragione piu' precisa di «non ha potuto guardare».
		if [ "$M_ESITO" = 0 ] || [ "$M_ESITO" = 1 ]; then
			esegui_maglia "C10 guasto innestato" true GIRA_C10G "$QUALE_MAGLIA"
		else
			salta_maglia "C10 guasto innestato" "C10 non ha potuto guardare: qui non c e il deposito"
		fi
	else
		salta_maglia C10 "il file non c e (o ce n e piu di uno)"
	fi

	# ⛔⛔ E ANCHE QUI LA MAGLIA SI CERCA PER PREFISSO, non si chiama per nome.
	#    `[M]` 26 agosto 2026, primo giro vero sulla macchina di prova: qui
	#    c era scritto `GIRA_C11`, una funzione **che non esiste** ⇒ la shell ha
	#    detto `command not found`, l esito e' stato **127**, e il giro e'
	#    proseguito come se niente fosse: ⛔ la famiglia veloce girava **senza
	#    la sua prima maglia**, e nel registro restava un numero che non
	#    significa niente.
	# ⚠ E si e' visto solo facendola girare: `bash -n` passa, perche la sintassi
	#   e' valida (`LEZIONI.md` §1.40).
	if trova_maglia c11; then
		esegui_maglia C11 false GIRA_MAGLIA "$QUALE_MAGLIA"
	else
		salta_maglia C11 "il file non c e (o ce n e piu di uno)"
	fi

	speso=$SECONDS; rimasto=$((TETTO_VELOCE - speso))
	local costo=$((COSTO_C1_GIRO * GIRI_VELOCE))
	if [ $rimasto -lt $costo ]; then
		salta_maglia "C1x$GIRI_VELOCE" "restano ${rimasto}s e ne servono ~${costo}s (tetto ${TETTO_VELOCE}s)"
	else
		local d
		for d in gnome; do
			esegui_maglia "C1($d)x$GIRI_VELOCE" false GIRA_C1 "$d" "$GIRI_VELOCE"
		done
	fi
	inf "⚠ tagliate dalla famiglia veloce, e dichiarato perche in testa a questo file:"
	inf "  C1 dal terzo giro in poi · C5 · C7 · C8 (tutt e due le prove) · C9 · il passo 0"
	inf "  ⛔ e le CINQUE NUOVE del 27 agosto: C2 · C3 · C4 · C6 · C8b"
	inf "  ⚠ e il tetto e PIENO: [M] 173 s su 180 (26 ago 2026, macchina di prova)."
	inf "    ⛔ C5 (71 s), C7 (26 s) e C9 (50 s) NON ci stanno: una maglia in piu"
	inf "    si SCAMBIA, non si somma (§5.1).  ⭐ C10 c e perche costa 0,04 s."
	inf "    ⛔ E le cinque nuove costano da sole piu di tutta questa famiglia:"
	inf "      una sessione da far nascere ciascuna.  ⇒ stanno in tutto e desktop-nuovo."
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LE CINQUE MAGLIE NUOVE, in un posto solo — 27 agosto 2026.
#
# ⛔ Stanno qui e non copiate due volte apposta: `famiglia_tutto` e
#    `famiglia_desktop_nuovo` le vogliono tutt e due, e due elenchi identici
#    sono due elenchi che il giorno dopo non lo sono piu' — e nessuno se ne
#    accorge, perche' tutt e due continuano a girare (`LEZIONI.md` §1.46).
#
# ⚠ E il `if` sul desktop non e' prudenza: `[R]` il prodotto sa avviare solo
#   GNOME (`src/sessione.c:778`).  Sulle altre scatole queste cinque
#   spenderebbero minuti per dire «non ho potuto guardare» — e un 3 che si
#   ripete per una decisione presa apposta e' il cugino del rosso perpetuo
#   (§1.49).  ⇒ Si SALTANO, e la ragione finisce nel registro.
# ═══════════════════════════════════════════════════════════════════════════
le_cinque_nuove() {
	local d=$1
	if [ "$d" != gnome ]; then
		salta_maglia "C2($d) C3 C4 C6 C8b" \
			"il prodotto sa avviare solo GNOME (src/sessione.c:778)"
		return
	fi

	# ⭐ C2 — una finestra si apre.  ⛔ Guarda IL PIXEL: il conto dei processi
	#   diceva 1 in tutt e due i casi (fasi/10… §7.4), e `--finestra-che-non-si-apre`
	#   lo dimostra invece di affermarlo — l applicazione resta VIVA e non dipinge.
	local P=(--attesa-palco "$TETTO_PALCO_C2C3")
	esegui_maglia "C2($d)" false GIRA_C2 "$d" "${P[@]}"
	esegui_maglia "C2($d) guasto innestato" true GIRA_C2 "$d" "${P[@]}" --applicazione-che-muore
	esegui_maglia "C2($d) guasto innestato (finestra cieca)" true GIRA_C2 "$d" "${P[@]}" --finestra-che-non-si-apre

	# ⭐ C3 — i fotogrammi arrivano e la scena CAMBIA.
	# ⚠ `--scena-ferma` NON e' un guasto innestato: e' il controllo NEGATIVO, e
	#   con la scena ferma C3 non deve dare rosso (`[M]` fasi/09… §3.1: a scena
	#   ferma escono 0,03 fotogrammi/s, ed e' un RISULTATO).
	esegui_maglia "C3($d)" false GIRA_C3 "$d" "${P[@]}"
	esegui_maglia "C3($d) scena ferma" false GIRA_C3 "$d" "${P[@]}" --scena-ferma
	esegui_maglia "C3($d) guasto innestato" true GIRA_C3 "$d" "${P[@]}" --fotogramma-ripetuto
	esegui_maglia "C3($d) guasto innestato (codificatore fermo)" true GIRA_C3 "$d" "${P[@]}" --codificatore-fermo

	# ⭐ C4 — il tasto arriva fino allo schermo.  ⛔ E' l unica maglia che
	#   giudica un PIXEL attraversando il prodotto ANDATA E RITORNO: C8 giudica
	#   il browser da solo, C5 giudica byte.
	esegui_maglia "C4($d)" false GIRA_C4 "$d"
	esegui_maglia "C4($d) guasto innestato" true GIRA_C4 "$d" --senza-tasto
	esegui_maglia "C4($d) guasto innestato (coda)" true GIRA_C4 "$d" --scena-sorda

	# ⭐⭐ C6 — si stacca e si ritrova.  ⚠ NON contraddice C7 `--solo-distacco`:
	#   C7 chiede «il figlio e' vivo?», C6 chiede «e quel che il figlio teneva in
	#   piedi si RITROVA?».  ⛔ Chi, vedendo C6 rossa, rendesse rossa anche C7
	#   «per coerenza», romperebbe la maglia sana.
	esegui_maglia "C6($d)" false GIRA_C6 "$d"
	esegui_maglia "C6($d) guasto innestato" true GIRA_C6 "$d" --uccidi-la-sessione

	# ⭐ C8b — e la stessa pagina si vede DAL CLIENTE.  ⛔ C8a non passa dal
	#   prodotto: guarda il browser dentro la sessione.  Questa guarda i pixel
	#   che arrivano al cliente.
	esegui_maglia "C8b($d)" false GIRA_C8B "$d"
	esegui_maglia "C8b($d) guasto innestato" true GIRA_C8B "$d" --senza-cura
}

famiglia_tutto() {
	# ⛔ Nessun tetto qui: e' la famiglia di prima di chiudere una fase, e §3.4
	#    dice UNA SCATOLA PER VOLTA, in fila, per il lucchetto della scheda.
	local d
	for d in $DESKTOP_NOTI; do
		log "scatola $d"
		esegui_maglia "passo0($d)" false GIRA_P0 "$d"
		esegui_maglia "C1($d)x10" false GIRA_C1 "$d" 10
		esegui_maglia "C8($d)" false GIRA_C8 "$d" --senza-sessione
		# ⭐⭐ E QUI STA LA META' CHE VALE: il guasto INNESTATO.
		#    §3.6 — «ogni prova della lista ha, obbligatoriamente, il suo
		#    guasto innestato, e quel caso va fatto girare, non immaginato».
		#    ⇒ E' questa riga che tiene in vita C13.
		esegui_maglia "C8($d) guasto innestato" true GIRA_C8 "$d" --senza-sessione --senza-cura

		# ⭐ C5 — il suono: ⛔ e' oggi l unica maglia che attraversa il prodotto
		#   da cima a fondo, perche giudica BYTE e non pixel (§7-bis.18).
		esegui_maglia "C5($d)" false GIRA_C5 "$d"
		esegui_maglia "C5($d) guasto innestato" true GIRA_C5 "$d" --senza-sorgente

		# ⭐ C7 — i residui.  ⚠ «si stacca soltanto» NON deve dare rosso (I4):
		#   il palco appartiene alla sessione e sopravvive alla disconnessione.
		esegui_maglia "C7($d)" false GIRA_C7 "$d"
		esegui_maglia "C7($d) si stacca soltanto" false GIRA_C7 "$d" --solo-distacco
		# ⚠ `--attesa-chiusura 10` non e' un tetto preso in prestito (§1.45): col
		#   guasto innestato si SA che il campo non tornera libero, e 10 s sono
		#   nove volte la chiusura misurata (`[M]` 1,13 s).
		esegui_maglia "C7($d) guasto innestato" true GIRA_C7 "$d" --lascia-un-processo --attesa-chiusura 10

		# ⭐ C9 — il registro.  Il guasto si innesta sui DATI VERI, sfregiando la
		#   copia in memoria della fetta: il registro sul disco non si tocca.
		esegui_maglia "C9($d)" false GIRA_C9 "$d"
		esegui_maglia "C9($d) guasto innestato" true GIRA_C9 "$d" --togli-nome tutto

		# ⭐⭐ E le cinque nuove del 27 agosto — solo su gnome, e la ragione
		#    sta scritta dentro `le_cinque_nuove`.
		le_cinque_nuove "$d"
	done
	# ⭐ `rete_intera`, cioe' **con C14** — e qui e' giusto: questa e' la
	#   famiglia di prima di chiudere una fase, i 786 s sono gia' a bilancio
	#   (`[M]` 786 su 1 704, §7-bis.16), e nessun'altra prova sta girando.
	famiglia_rete_intera
}

famiglia_desktop_nuovo() {
	local nuovo=$1 d
	log "il desktop nuovo: $nuovo"
	esegui_maglia "passo0($nuovo)" false GIRA_P0 "$nuovo"
	esegui_maglia "C1($nuovo)x10" false GIRA_C1 "$nuovo" 10
	esegui_maglia "C8($nuovo)" false GIRA_C8 "$nuovo" --senza-sessione
	esegui_maglia "C8($nuovo) guasto innestato" true GIRA_C8 "$nuovo" --senza-sessione --senza-cura
	esegui_maglia "C5($nuovo)" false GIRA_C5 "$nuovo"
	esegui_maglia "C5($nuovo) guasto innestato" true GIRA_C5 "$nuovo" --senza-sorgente
	esegui_maglia "C7($nuovo)" false GIRA_C7 "$nuovo"
	esegui_maglia "C7($nuovo) guasto innestato" true GIRA_C7 "$nuovo" --lascia-un-processo --attesa-chiusura 10
	esegui_maglia "C9($nuovo)" false GIRA_C9 "$nuovo"
	esegui_maglia "C9($nuovo) guasto innestato" true GIRA_C9 "$nuovo" --togli-nome tutto
	# ⭐⭐ Le cinque nuove.  ⚠ Oggi, su un desktop nuovo che non e' gnome, si
	#    saltano tutte e la ragione finisce nel registro — ⛔ ed e' proprio il
	#    posto dove la si vuole leggere: il giorno che il prodotto sapra' avviare
	#    un secondo desktop, questa riga comincia a girare DA SOLA, senza che
	#    nessuno debba ricordarsi di aggiungerla.
	le_cinque_nuove "$nuovo"
	log "e la REGRESSIONE sui vecchi — ⭐ senza riscrivere una riga della lista"
	for d in $DESKTOP_NOTI; do
		[ "$d" = "$nuovo" ] && continue
		esegui_maglia "C1($d)x$GIRI_VELOCE" false GIRA_C1 "$d" "$GIRI_VELOCE"
	done
	# ⭐⭐ E QUI C14 SERVE PIU' CHE MAI, non meno: con una scatola in piu' la
	#    domanda *«le scatole non si disturbano»* ha una risposta nuova, e la
	#    mappa delle porte di `11-accendi.sh` ha una voce nuova da assegnare.
	famiglia_rete_intera
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LE DUE META', CABLATE — e non e' una comodita': e' la cura del guasto
#      dichiarato in `DECISIONI.md` §4.6-novemdecies.
#
# ⛔ Fin qui il gancio aveva due meta' su due macchine e **soltanto una delle due
#    era agganciata a qualcosa**: sul portatile c'e' il deposito e c'e' il
#    `pre-push`, ma li' possono girare solo C10, C12, C13 — `[M]` un secondo.
#    Le maglie vere vogliono le scatole e la scheda, cioe' la macchina di prova,
#    ⛔ dove non c'e' git e quindi **non le fa partire niente**: oggi le lancia
#    una persona a mano.  ⇒ E' il modo esatto in cui queste reti muoiono in
#    silenzio (§4.2): esistono, sono perfette, e non parte niente.
#
# ⭐ Da qui in poi: **si decide dove c'e' il deposito, si esegue dove ci sono le
#   scatole, e la memoria torna indietro in un posto solo.**
# ═══════════════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# ⭐ LA META' DI QUI — le maglie che vogliono il DEPOSITO e non le scatole.
#
# ⚠ Sono TRE, e sono sempre le stesse qualunque sia la famiglia: C10, il suo
#   guasto innestato, ⭐ e **C15** — che legge la memoria appena unita e dice se
#   la meta' di LA' sta girando davvero (vedi in fondo a questa funzione).
#   ⛔ Non e' una scelta di comodo — §4.6-unetvicies: sulla
#   macchina di prova C10 non puo' che dire «non ho potuto guardare», quindi
#   **il guasto innestato che tiene in vita C13 puo' nascere solo qui.**
#   ⇒ Se questa meta' non girasse, C13 avrebbe come unico cibo dei giri in cui
#     nessun guasto e' mai stato iniettato, e direbbe rosso per sempre.
# ---------------------------------------------------------------------------
meta_locale() {
	if trova_maglia c10; then
		esegui_maglia C10 false GIRA_MAGLIA "$QUALE_MAGLIA"
		if [ "$M_ESITO" = 0 ] || [ "$M_ESITO" = 1 ]; then
			esegui_maglia "C10 guasto innestato" true GIRA_C10G "$QUALE_MAGLIA"
		else
			salta_maglia "C10 guasto innestato" "C10 non ha potuto guardare"
		fi
	elif [ "$QUALE_MAGLIA" = TROPPE ]; then
		salta_maglia C10 "ce ne sono PIU DI UNA con questo numero: non tiro a indovinare"
	else
		salta_maglia C10 "il file non c e"
	fi

	# ═══════════════════════════════════════════════════════════════════
	# ⭐⭐⭐ E C15, **QUI E SOLO QUI FRA LE DUE META'** — ed e' il posto che
	#      la rende una maglia invece di un ornamento.
	#
	# ⛔ C15 legge la MEMORIA UNITA, e la memoria unita nasce due righe fa:
	#    `meta_remota` ha appena riportato e accodato le righe della macchina
	#    di prova (`unisci_registri`).  ⇒ Un giro remoto riuscito la fa
	#    diventare verde nello stesso istante in cui succede.
	# ⛔ E se la meta' remota ha detto 3, l'unione NON e' avvenuta: C15 legge
	#    il registro di prima, ed e' giusto — quel giro sulle scatole non c'e'
	#    stato.  ⇒ ⭐ E' cosi' che «un 3 frequente» (§5.2) diventa una riga
	#    rossa invece di restare un'impressione.
	#
	# ⚠⚠ E VA DETTO CHE COSA COMPRA, perche' e' una decisione e non un
	#    dettaglio: **un rosso di C15 BLOCCA l'invio**, mentre il 3 della meta'
	#    remota non lo blocca.  ⛔ Sembra un'incoerenza e non lo e': §5.2 dice
	#    che *«il singolo 3 e' neutro; un 3 FREQUENTE e' un guasto del banco»*.
	#    ⇒ La macchina di prova spenta stamattina non ferma nessuno; ⛔ la
	#      macchina di prova spenta da otto giorni ferma l'invio, perche' a
	#      quel punto si sta spingendo codice che nessuno ha misurato.
	#    ⭐ E si torna verde con un comando, che C15 stessa stampa.
	# ═══════════════════════════════════════════════════════════════════
	if trova_maglia c15; then
		esegui_maglia C15 false GIRA_MAGLIA "$QUALE_MAGLIA"
	elif [ "$QUALE_MAGLIA" = TROPPE ]; then
		salta_maglia C15 "ce ne sono PIU DI UNA con questo numero: non tiro a indovinare"
	else
		salta_maglia C15 "il file non c e"
	fi
}

# ---------------------------------------------------------------------------
SSHPW=""
sshpw() { python3 "$SSHPW" "$@"; }

# ⚠ Un'annotazione, non una maglia: dice se la DELEGA ha funzionato.
#   ⛔ Serve perche' altrimenti una macchina di prova spenta sarebbe invisibile:
#     la meta' locale scriverebbe la sua riga verde, C12 direbbe «il gancio e'
#     vivo», C13 direbbe «la rete sa dare rosso» — ⛔ e sulle scatole non
#     sarebbe girato niente per settimane.  ⇒ Con questa riga nel registro,
#     §5.2 morde: «un 3 frequente e' un guasto del banco, non un esito».
annota_remota() {
	local esito=$1 secondi=$2 nota=$3
	[ -n "$eseguiti_json" ] && eseguiti_json="$eseguiti_json,"
	eseguiti_json="$eseguiti_json{\"nome\":\"la meta remota\",\"esito\":$esito,\"secondi\":$secondi,\"guasto_innestato\":false,\"macchina\":$(json_stringa "$RETE11_REMOTA"),\"nota\":$(json_stringa "$nota")}"
}

# ---------------------------------------------------------------------------
# ⛔⛔ L'ATTESA NON LA FA QUESTA MACCHINA, e non e' un dettaglio.
#
# Un `systemctl is-active` ogni cinque secondi per mezz'ora sono **quattrocento
# connessioni ssh**, ciascuna `[M]` 0,28 s: ⇒ due minuti buttati e quattrocento
# richieste di password.  ⛔ E nemmeno un'attesa sola lunga: un comando che sta
# in ssh diretto oltre il minuto e mezzo non si porta a casa.
# ⇒ Un minuto per volta, e ad aspettare e' la macchina di prova.
#
# ⚠ E si aspetta **il file d'esito**, non lo stato di systemd: un'unita'
#   transitoria che riesce SPARISCE, e «sparita» somiglia a «non partita»
#   (`11-gancio-remoto.sh`, e c'e' scritto perche').
# ---------------------------------------------------------------------------
#
# ⛔⛔ E SI GUARDA ANCHE SE L'UNITA' E' ANCORA VIVA — `[M]` 27 agosto 2026, e
#     l'ha preso il guasto innestato di questo meccanismo, non una lettura.
#
# La prima stesura aspettava **solo** il file d'esito.  ⇒ Se l'unita' moriva
# senza scriverlo — il file del lanciatore non c'e', `bash` non parte, systemd
# la marca `failed` — ⛔ **questa funzione restava ad aspettare 2 400 secondi**
# un file che non sarebbe arrivato mai.  ⚠ E il sintomo era quello che inganna:
# non un errore, ma un invio «lento» (la stessa forma di `sshpw.py`, dove c'e'
# scritta per esteso).
#
# ⭐ E L'ORDINE DELLE DUE DOMANDE NON E' LIBERO: **prima il file, poi l'unita'.**
#   Il lanciatore scrive l'esito **prima** di uscire ⇒ se l'unita' e' sparita, il
#   file c'e' gia'.  ⛔ Chiedendo prima dell'unita' ci sarebbe una fessura in cui
#   un giro riuscito verrebbe dichiarato morto.
attendi_remoto() {
	local esito_f=$1 tetto=$2 speso=0 risposta=""
	while [ "$speso" -lt "$tetto" ]; do
		# ⛔⛔ E IL PASSO E' DI 2 SECONDI, NON DI 5 — ed e' un conto sul tetto,
		#    non un gusto.  `[M]` §5.1: la famiglia veloce e' a **173 s su 180**,
		#    cioe' sette secondi di margine.  ⚠ Chi aspetta paga, oltre al giro,
		#    l'ARROTONDAMENTO di questa domanda: col passo a 5 s si potevano
		#    perdere 5 s in fondo, e 173 + 5 + il giro dei comandi **sfonda**.
		#    ⇒ Col passo a 2 s l'arrotondamento sta dentro il margine.
		# ⚠ La lista dei giri la costruisce il portatile (`seq`), cosi' la riga
		#   che arriva alla macchina di prova non ha niente da espandere.
		risposta=$(sshpw "for i in $(seq 1 30 | tr '\n' ' '); do [ -f $esito_f ] && break; systemctl is-active --quiet $UNITA_REMOTA || break; sleep 2; done; cat $esito_f 2>/dev/null || { systemctl is-active --quiet $UNITA_REMOTA && echo ANCORA || echo MORTA; }" 2>/dev/null \
			| tr -d '\r' | grep -E '^[0-9]+$|^ANCORA$|^MORTA$' | tail -n 1)
		case "$risposta" in
		''|ANCORA) : ;;
		*) printf '%s' "$risposta"; return 0 ;;
		esac
		speso=$((speso + 60))
		inf "  … la meta' remota sta ancora girando (${speso}s)"
	done
	printf 'ATTESA'
	return 1
}

# ---------------------------------------------------------------------------
# ⭐ LA META' DI LA' — si lancia, si aspetta, si legge, e si riporta.
#    Riempie R_ESITO (0 verde · 1 rosso · 3 non ho potuto guardare) e R_NOTA.
# ---------------------------------------------------------------------------
R_ESITO=3
R_NOTA=""
meta_remota() {
	local fam=$1 inn=$2
	local log="$RETE11_REMOTA/$UNITA_REMOTA.log"
	local esito_f="$RETE11_REMOTA/$UNITA_REMOTA.esito"
	# ⚠ `sudo` serve perche' le maglie delle scatole passano da `podman`, e il
	#   registro di la' e' di root da sempre.  ⛔ E il prezzo va detto: se il
	#   gancio girasse la' da `nicfio`, l'accodamento al registro fallirebbe con
	#   «Permission denied» e il giro **non lascerebbe traccia** pur avendo
	#   misurato tutto.  `[M]` 27 agosto 2026, provato.
	local S="sudo -S -p 'Password sudo: '"
	local opz="" risposta="" prima dopo

	[ "$SECCO" = 1 ] && opz="$opz --secco"
	[ -n "$SCATOLA_CHIESTA" ] && opz="$opz --scatola $SCATOLA_CHIESTA"

	prima=$SECONDS
	# ⛔ Il log e il file d'esito si cancellano PRIMA: un esito vecchio letto
	#    come se fosse di questo giro e' un giro che riferisce di un altro.
	sshpw "$S systemctl reset-failed $UNITA_REMOTA 2>/dev/null; $S rm -f $log $esito_f" >/dev/null 2>&1

	inf "lancio: $RETE11_REMOTA/11-gancio.sh gira --famiglia $fam --innesco $inn$opz"
	if ! sshpw "$S systemd-run --unit=$UNITA_REMOTA --property=StandardOutput=append:$log --property=StandardError=append:$log --property=WorkingDirectory=$RETE11_REMOTA bash $RETE11_REMOTA/11-gancio-remoto.sh $esito_f gira --famiglia $fam --innesco $inn$opz" >/dev/null 2>&1; then
		dopo=$SECONDS
		R_ESITO=3
		R_NOTA="non sono riuscito a lanciare il giro sulla macchina di prova"
		ko "⛔ $R_NOTA"
		inf "  ⇒ e' un «non ho potuto guardare» (esito 3), ⛔ NON un verde:"
		inf "    la riga di registro lo porta scritto, e §5.2 dice che un 3"
		inf "    ripetuto e' un guasto del banco"
		M_SECONDI=$((dopo - prima))
		return 3
	fi

	risposta=$(attendi_remoto "$esito_f" "$ATTESA_REMOTA")
	dopo=$SECONDS
	M_SECONDI=$((dopo - prima))

	# ⭐ Il log si porta a casa con scp (`--get`), ⛔ mai catturando lo stdout di
	#   un `cat` remoto: li' dentro finisce anche la richiesta di password
	#   (`fondamenta/strumenti/sshpw.py`, e c'e' scritto perche').
	local tana
	tana=$(mktemp -d)
	sshpw --get "$log" "$tana/remoto.log" >/dev/null 2>&1
	if [ -s "$tana/remoto.log" ]; then
		log "quel che ha detto la macchina di prova"
		sed 's/^/  | /' "$tana/remoto.log"
	fi

	# ⛔ E i due modi di non sapere sono DUE, e vanno detti separati: «non ha
	#    finito» e «e' morta senza dire niente» si curano in posti diversi.
	if [ "$risposta" = ATTESA ] || [ "$risposta" = MORTA ]; then
		R_ESITO=3
		if [ "$risposta" = MORTA ]; then
			R_NOTA="l'unita' della meta' remota e' morta senza scrivere un esito"
			ko "⛔ $R_NOTA"
			inf "  ⇒ guarda il log qui sopra e «systemctl status $UNITA_REMOTA»"
			inf "    sulla macchina di prova: il giro non e' nemmeno partito"
		else
			R_NOTA="la meta' remota non ha finito entro ${ATTESA_REMOTA}s"
			ko "⛔ $R_NOTA"
		fi
		rm -rf "$tana"
		return 3
	fi

	# ⭐⭐ E ADESSO LA MEMORIA TORNA INDIETRO — l'altra meta' del problema.
	unisci_registri "$tana"
	rm -rf "$tana"

	case "$risposta" in
	0) R_ESITO=0; R_NOTA="la meta' remota e' verde" ;;
	1) R_ESITO=1; R_NOTA="⛔ la meta' remota ha dato ROSSO" ;;
	*) R_ESITO=3; R_NOTA="la meta' remota e' uscita $risposta (terreno, o uso sbagliato)" ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⭐⭐ UNA MEMORIA SOLA — e sta QUI, sul portatile.
#
# ⛔ Non e' una preferenza: e' l'unico posto dove le due maglie che leggono
#    quella memoria sanno giudicare.  C12 ha bisogno del deposito git per sapere
#    dove stanno i ganci, e sulla macchina di prova esce **2** — e §7-bis.16 dice
#    che *e' la risposta giusta*.  ⇒ Il portatile e' dove la rete si guarda allo
#    specchio; la macchina di prova e' dove **esegue**.
# ⚠ Il registro di la' NON si cancella e NON si svuota: resta la memoria locale
#   di quella macchina, e serve a chi diagnostica li'.  Qui se ne prende copia.
# ---------------------------------------------------------------------------
unisci_registri() {
	local tana=$1
	local remoto="$RETE11_REMOTA/11-gancio-registro.jsonl"
	sshpw --get "$remoto" "$tana/registro-remoto.jsonl" >/dev/null 2>&1
	if [ ! -s "$tana/registro-remoto.jsonl" ]; then
		ko "⚠ non sono riuscito a riportare il registro della macchina di prova"
		inf "  ⇒ il giro di la' e' successo davvero, ma qui non se ne saprebbe"
		inf "    niente: C13 non lo vedrebbe.  ⛔ E' un guasto, non un dettaglio"
		return 3
	fi
	python3 "$QUI/11-registro-unisci.py" "$REGISTRO" "$tana/registro-remoto.jsonl"
}

# ---------------------------------------------------------------------------
scrivi_registro() {
	local famiglia=$1 innesco=$2 sforato=$3 secondi=$4 rosso=$5 guasto=$6
	shift 6
	{
		printf '{'
		printf '"istante":%s,' "$(json_stringa "$(date -Is)")"
		printf '"dove":%s,' "$(json_stringa "$DOVE")"
		printf '"innesco":%s,' "$(json_stringa "$innesco")"
		printf '"famiglia":%s,' "$(json_stringa "$famiglia")"
		printf '"secco":%s,' "$([ "$SECCO" = 1 ] && echo true || echo false)"
		printf '"cambiati":%s,' "$(json_elenco "$@")"
		printf '"maglie":[%s],' "$eseguiti_json"
		printf '"guasto_innestato":%s,' "$guasto"
		printf '"ha_dato_rosso":%s,' "$rosso"
		printf '"secondi":%s,' "$secondi"
		printf '"tetto":%s,' "$([ "$famiglia" = funziona ] && echo "$TETTO_VELOCE" || echo null)"
		printf '"sforato":%s' "$sforato"
		printf '}\n'
	} >> "$REGISTRO"
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ E SI GUARDA SE LA RIGA E' DAVVERO ANDATA GIU'.
	#
	# `[M]` 27 agosto 2026, provato sulla macchina di prova: il registro la' e'
	# **di root** — l'hanno scritto i giri lanciati con `systemd-run`, e i modi
	# sono `-rw-r--r--`.  ⇒ Un giro lanciato a mano da `nicfio` fa un `>>` che
	# fallisce con *«Permission denied»*, ⛔ **e questo script tira avanti**:
	# `set -uo pipefail` non ha la `e`, e la riga successiva stampa «nessun
	# rosso».
	# ⇒ ⛔ Un giro che ha misurato tutto, non ha lasciato traccia, e ha detto
	#   che era andato bene.  ⚠ E il danno non e' nel giro: e' che C12 e C13
	#   vivono di quella traccia — la rete perderebbe la memoria senza che
	#   nessuno se ne accorga, che e' §4.2 di nuovo.
	# ⭐ Non si ripara il permesso da qui (non e' mestiere di un banco): si DICE.
	# ═══════════════════════════════════════════════════════════════════
	if [ ! -w "$REGISTRO" ] && [ -e "$REGISTRO" ]; then
		ko "⛔⛔ NON HO POTUTO SCRIVERE NEL REGISTRO: $REGISTRO"
		inf "  ⇒ questo giro ha misurato tutto e ⛔ NON HA LASCIATO TRACCIA."
		inf "    C12 dira' che il gancio non gira e C13 che nessuno la mette"
		inf "    alla prova, e tutt'e due avranno ragione da un punto di vista"
		inf "    sbagliato."
		inf "  ⚠ e' di $(stat -c %U "$REGISTRO" 2>/dev/null): o lo si lancia con"
		inf "    lo stesso utente, o si cambia il proprietario del file"
		return 1
	fi
}

# ---------------------------------------------------------------------------
# ⛔⛔ IL GIT SERVE PER **DECIDERE**, NON PER **GIRARE** — e la differenza e' una
#     cosa che si e' scoperta al primo giro vero, `[M]` 26 agosto 2026.
#
# ⚠ Le due meta' di questo gancio vivono in due posti diversi:
#     · DECIDERE che cosa far girare vuole il deposito ⇒ sta sul portatile
#     · FAR GIRARE vuole le scatole e la scheda grafica ⇒ sta sulla macchina
#       di prova, ⛔ **dove il deposito NON c e**
#   ⇒ La prima stesura pretendeva git sempre, e usciva **2** («terreno cattivo»)
#     sull unica macchina in grado di eseguire le maglie: cioe' ⛔ **il gancio
#     non poteva essere cronometrato dove gira davvero.**
#
# ⭐ Quindi: se la famiglia e' CHIESTA PER NOME non c e' niente da decidere, e il
#   deposito non serve.  Se non e' chiesta, serve — e allora si dice.
# ⚠ E il registro segna sempre quale delle due strade e' stata presa, cosi' chi
#   legge sa se quel giro ha guardato dei percorsi o ha ubbidito a un nome.
# ---------------------------------------------------------------------------
SECCO=0
AZIONE=${1:-decidi}
shift 2>/dev/null || true
FAMIGLIA_CHIESTA=""
SCATOLA_CHIESTA=""
SOLO_QUI=0
INNESCO="mano"
# ⛔⛔ E GLI ARGOMENTI CHE NON SONO OPZIONI SI METTONO DA PARTE, non si buttano.
#
# `[M]` 26 agosto 2026, e l'ha preso il banco di prova al primo giro: la prima
# stesura faceva `shift` su TUTTO dentro questo ciclo, ⇒ quando poi `installa`
# andava a leggere `$1` non c era piu' niente e ripiegava sul predefinito.
# ⛔ Risultato: `installa pre-commit` **installava `pre-push`**, e diceva «OK».
# ⚠ Cioe' il gancio faceva una cosa diversa da quella chiesta e riferiva
#   riuscita — la stessa famiglia d errore di `LEZIONI.md` §1.46, e questa volta
#   dentro il gancio stesso.
RESTO=()
while [ $# -gt 0 ]; do
	case "$1" in
	--secco)    SECCO=1 ;;
	--famiglia) FAMIGLIA_CHIESTA=${2:-}; shift ;;
	# ⛔⛔ E SI PUO CHIEDERE UNA SCATOLA SOLA, ed e una necessita, non un lusso.
	#    `[M]` 26 agosto 2026: la famiglia `tutto` gira le maglie del PRODOTTO su
	#    tutt e quattro i desktop, ⛔ ma il prodotto oggi ne sa accendere UNO
	#    (KDE e la fase 12, XFCE e LXQt la 13).  ⇒ Sulle altre tre le maglie del
	#    prodotto non possono che dire «non ho potuto guardare», e un giro che
	#    per tre quarti non giudica costa un ora e insegna niente.
	# ⚠ E NON si mette un «se il desktop e gnome» dentro le famiglie: quello
	#   sarebbe un eccezione per compositore travestita (`DECISIONI.md` §5.1-bis).
	#   ⭐ Qui e chi lancia a dire su quale scatola vuole girare, e resta scritto
	#     nel registro — cosi il giorno che il prodotto sapra accendere KDE non
	#     c e niente da togliere: si smette di passare l opzione.
	--scatola)  DESKTOP_NOTI=${2:-}; SCATOLA_CHIESTA=${2:-}; shift ;;
	--innesco)  INNESCO=${2:-mano}; shift ;;
	# ⚠ Il nome dell'unita' della meta' remota — serve a far girare due giri
	#   insieme senza pestarsi l'unita' e il log.  ⛔ Non decide che cosa gira.
	--unita)    UNITA_REMOTA=${2:-$UNITA_REMOTA}; shift ;;
	# ⚠ `installa … --solo-qui`: il gancio installato fa girare SOLO la meta'
	#   del portatile.  ⛔ E' un ripiego dichiarato, non il predefinito — vedi
	#   `installa`, dove c'e' scritto che cosa costa.
	--solo-qui) SOLO_QUI=1 ;;
	*)          RESTO+=("$1") ;;
	esac
	shift
done
set -- "${RESTO[@]+"${RESTO[@]}"}"

# ⛔ Adesso che si sa se la famiglia e stata chiesta per nome, si puo dire se il
#    deposito serviva davvero.
if [ -z "$RADICE" ] && [ -z "$FAMIGLIA_CHIESTA" ]; then
	ko "non sono dentro un deposito git, e nessuna famiglia e stata chiesta per nome"
	ko "⇒ non ho modo di DECIDERE che cosa far girare (--famiglia <nome> non ne ha bisogno)"
	exit 2
fi

case "$AZIONE" in

decidi|gira)
	mapfile -t ELENCO < <(cambiati "$INNESCO")
	if [ -n "$FAMIGLIA_CHIESTA" ]; then
		FAMIGLIA="$FAMIGLIA_CHIESTA"
		MOTIVO="chiesta per nome"
	else
		FAMIGLIA=$(decidi_famiglia ELENCO)
		MOTIVO=$(perche_famiglia "$FAMIGLIA")
	fi

	log "Il gancio — innesco: $INNESCO"
	inf "file cambiati: ${#ELENCO[@]}"
	for f in "${ELENCO[@]:0:12}"; do inf "  · $f"; done
	[ ${#ELENCO[@]} -gt 12 ] && inf "  … e altri $(( ${#ELENCO[@]} - 12 ))"
	inf "famiglia: ${FAMIGLIA%%:*}   ⇐ $MOTIVO"
	[ "${FAMIGLIA%%:*}" = funziona ] && inf "tetto: ${TETTO_VELOCE}s (⛔ e se sfora si tagliano prove, non si alza il tetto)"

	if [ "$AZIONE" = decidi ]; then
		exit 0
	fi

	if [ "${FAMIGLIA%%:*}" = niente ]; then
		inf "⭐ non parte niente — e non e' pigrizia: un gancio che gira quando"
		inf "  non serve e' un gancio che qualcuno spegnera'"
		exit 0
	fi

	SECONDS=0
	case "${FAMIGLIA%%:*}" in
	funziona)      log "famiglia FUNZIONA"; famiglia_veloce ;;
	# ⛔ E LA RIGA CHE SI STAMPA DICE IL COSTO VERO.  Qui c'era scritto
	#    «C11-C14 + C10, che non accende niente»: ⛔ era la stessa promessa
	#    falsa del commento, ma **stampata**, cioe' vista da qualcuno nel
	#    momento esatto in cui contava.
	rete)          log "la RETE — C10, C11, C12, C13, C15  ⭐ [M] ~11 s, e nessuna accende una sessione"; famiglia_rete ;;
	rete-intera)   log "la RETE **PIU' C14** — ⛔ [M] ~800 s, e si prende le QUATTRO scatole"; famiglia_rete_intera ;;
	tutto)         log "TUTTO — prima di chiudere una fase"; famiglia_tutto ;;
	desktop-nuovo) famiglia_desktop_nuovo "${FAMIGLIA##*:}" ;;
	*)             ko "famiglia sconosciuta: $FAMIGLIA"; exit 2 ;;
	esac
	DURATA=$SECONDS

	# ⛔ «ha dato rosso» vuol dire ESITO 1 — un giudizio.  ⚠ Il 3 NON e' un
	#    rosso (§4.5), e contarlo come tale renderebbe C13 verde per sbaglio.
	ROSSO=false
	GUASTO=false
	printf '%s' "$eseguiti_json" | grep -q '"esito":1' && ROSSO=true
	printf '%s' "$eseguiti_json" | grep -q '"guasto_innestato":true' && GUASTO=true

	SFORATO=false
	if [ "${FAMIGLIA%%:*}" = funziona ] && [ "$DURATA" -gt "$TETTO_VELOCE" ]; then
		SFORATO=true
	fi

	scrivi_registro "${FAMIGLIA%%:*}" "$INNESCO" "$SFORATO" "$DURATA" "$ROSSO" "$GUASTO" "${ELENCO[@]}"

	log "esito del giro"
	inf "durata: ${DURATA}s"
	if [ "$SFORATO" = true ]; then
		ko "⛔ HA SFORATO IL TETTO: ${DURATA}s contro ${TETTO_VELOCE}s"
		inf "⇒ §5.1: si TAGLIANO PROVE, non si alza il tetto.  ⚠ E questo e'"
		inf "  adesso un [M], non piu' un [?]: il numero e' nel registro"
	fi
	if [ "$SECCO" = 1 ]; then
		inf "⚠ giro a VUOTO: non ha misurato niente, e la riga di registro porta"
		inf "  «secco: true» — ⛔ C12 e C13 la buttano via, e devono"
		exit 0
	fi
	if [ "$ROSSO" = true ]; then
		# §5.2, la politica del rosso: rosso in FUNZIONA BLOCCA.
		ko "⛔ ROSSO — §5.2: si ripara prima di andare avanti, non si archivia"
		inf "  come «poi vediamo».  ⚠ E un rosso intermittente E' un rosso:"
		inf "  non si ripete la prova sperando nel verde"
		exit 1
	fi
	ok "nessun rosso"
	exit 0
	;;

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ `remoto` — IL GIRO INTERO, sulle due macchine
#
# ⛔⛔ E L'ORDINE DEI PASSI NON E' LIBERO: prima LA', poi QUI.
#
# La meta' remota scrive la sua riga sulla macchina di prova; quella riga deve
# poter essere accodata al registro di qui, e `11-registro-unisci.py` accoda
# **solo cio' che e' piu' nuovo della riga piu' recente gia' presente**.
# ⇒ Se la riga locale si scrivesse per prima, sarebbe piu' recente di quella
#   remota, ⛔ **e la riga remota non entrerebbe mai** — cioe' il giro sulle
#   scatole sarebbe girato davvero e la memoria non ne saprebbe niente.
# ⇒ Percio': si esegue di la', si riporta, e **solo alla fine** si scrive la
#   riga di qui, che e' l'ultima anche in ordine di tempo.
# ═══════════════════════════════════════════════════════════════════════════
remoto)
	# ⛔ Questa e' la meta' che DECIDE: senza deposito non ha niente da guardare.
	if [ -z "$RADICE" ]; then
		ko "«remoto» si lancia dal PORTATILE, dove c'e' il deposito"
		ko "⇒ qui il deposito non c'e': se questa e' la macchina di prova, il"
		ko "  comando e' «gira --famiglia <nome>», e lo lancia il portatile"
		exit 2
	fi
	SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"
	if [ ! -f "$SSHPW" ]; then
		ko "non trovo $SSHPW: senza non si arriva alla macchina di prova"
		exit 2
	fi

	mapfile -t ELENCO < <(cambiati "$INNESCO")
	if [ -n "$FAMIGLIA_CHIESTA" ]; then
		FAMIGLIA="$FAMIGLIA_CHIESTA"
		MOTIVO="chiesta per nome"
	else
		FAMIGLIA=$(decidi_famiglia ELENCO)
		MOTIVO=$(perche_famiglia "$FAMIGLIA")
	fi

	log "Il gancio, LE DUE META' — innesco: $INNESCO"
	inf "decide QUI ($DOVE, dove c'e' il deposito)"
	inf "esegue LA'  ($RETE11_REMOTA, dove ci sono le scatole e la scheda)"
	inf "file cambiati: ${#ELENCO[@]}"
	for f in "${ELENCO[@]:0:12}"; do inf "  · $f"; done
	[ ${#ELENCO[@]} -gt 12 ] && inf "  … e altri $(( ${#ELENCO[@]} - 12 ))"
	inf "famiglia: ${FAMIGLIA%%:*}   ⇐ $MOTIVO"

	if [ "${FAMIGLIA%%:*}" = niente ]; then
		inf "⭐ non parte niente, ne' qui ne' la' — e non e' pigrizia: un gancio"
		inf "  che gira quando non serve e' un gancio che qualcuno spegnera'"
		inf "  ⇒ ⭐ ed e' anche il motivo per cui il prezzo di questa strada NON"
		inf "    e' «ogni invio diventa lento»: gli invii che toccano solo i"
		inf "    documenti costano **zero secondi**"
		exit 0
	fi

	SECONDS=0

	# 1 · LA' — le maglie vere, sulle scatole
	log "la meta' di LA' — le scatole e la scheda"
	meta_remota "${FAMIGLIA%%:*}" "$INNESCO-remoto"
	R_SECONDI=$M_SECONDI
	annota_remota "$R_ESITO" "$R_SECONDI" "$R_NOTA"

	# 2 · QUI — le maglie che vogliono il deposito
	log "la meta' di QUI — il deposito"
	meta_locale

	DURATA=$SECONDS

	ROSSO=false
	GUASTO=false
	printf '%s' "$eseguiti_json" | grep -q '"esito":1' && ROSSO=true
	printf '%s' "$eseguiti_json" | grep -q '"guasto_innestato":true' && GUASTO=true

	# ⚠ E il tetto si giudica sul tempo che ASPETTA CHI LAVORA — cioe' tutto il
	#   giro, l'andata e il ritorno compresi.  ⛔ La riga scritta di la' porta un
	#   altro numero, ed e' giusto che siano due: quello dice quanto costano le
	#   maglie, questo quanto costa l'invio.
	SFORATO=false
	if [ "${FAMIGLIA%%:*}" = funziona ] && [ "$DURATA" -gt "$TETTO_VELOCE" ]; then
		SFORATO=true
	fi

	scrivi_registro "${FAMIGLIA%%:*}" "$INNESCO" "$SFORATO" "$DURATA" "$ROSSO" "$GUASTO" "${ELENCO[@]}"

	log "esito del giro, tutt'e due le meta'"
	inf "durata totale (quel che aspetta chi manda): ${DURATA}s"
	inf "di cui la meta' remota: ${R_SECONDI}s"
	inf "la meta' remota: $R_NOTA"
	if [ "$SFORATO" = true ]; then
		ko "⛔ HA SFORATO IL TETTO: ${DURATA}s contro ${TETTO_VELOCE}s"
		inf "⇒ §5.1: si TAGLIANO PROVE, non si alza il tetto"
	fi
	if [ "$SECCO" = 1 ]; then
		inf "⚠ giro a VUOTO: non ha misurato niente, e le righe di registro —"
		inf "  quella di qui e quella di la' — portano «secco: true».  ⛔ C12 e"
		inf "  C13 le buttano via, e devono"
		exit 0
	fi
	if [ "$ROSSO" = true ]; then
		ko "⛔ ROSSO — §5.2: si ripara prima di andare avanti"
		exit 1
	fi
	if [ "$R_ESITO" = 3 ]; then
		inf "⚠ e non blocca, per scelta dichiarata: un gancio che ferma il"
		inf "  lavoro perche' una SECONDA macchina non risponde e' un gancio che"
		inf "  qualcuno spegnera'.  ⛔ Ma il «non ho potuto guardare» resta"
		inf "  scritto nel registro, e §5.2 dice che un 3 ripetuto e' un guasto"
		exit 0
	fi
	ok "nessun rosso, ne' qui ne' la'"
	exit 0
	;;

installa)
	QUALE=${1:-pre-push}
	case "$QUALE" in
	pre-commit|pre-push) : ;;
	# ⛔ Un nome che non si conosce NON si ignora ripiegando sul predefinito:
	#    si rifiuta.  Ripiegare vorrebbe dire installare una cosa diversa da
	#    quella chiesta e dire «OK» — il difetto che questo file ha gia avuto.
	*) ko "gancio sconosciuto: «$QUALE» — sono pre-commit o pre-push"; exit 2 ;;
	esac
	# ⚠ E la scelta del predefinito e' DICHIARATA, non ovvia.
	#   §5.1 dice «si tocca src/», che suona come un commit.  ⛔ Ma la famiglia
	#   veloce costa fino a tre minuti, e tre minuti a OGNI commit sono
	#   esattamente la cosa che §5.1 stessa dice che fa spegnere un gancio.
	#   ⇒ Predefinito `pre-push`: si paga una volta per spinta invece che una
	#     volta per commit.  Chi vuole l altro lo chiede per nome, e sa perche.
	CARTELLA=$(cartella_ganci)
	[ -d "$CARTELLA" ] || mkdir -p "$CARTELLA"
	# ⚠ Si chiamava `DOVE`, ed e' stato rinominato: `DOVE` adesso e' il nome
	#   della macchina, e finisce in ogni riga di registro.  ⛔ Due variabili
	#   con lo stesso nome in uno script senza `local` sono un valore che
	#   cambia sotto i piedi di chi non guarda.
	PERCORSO="$CARTELLA/$QUALE"
	# ═══════════════════════════════════════════════════════════════════
	# ⛔⛔ E QUEL CHE IL GANCIO INSTALLATO CHIAMA E' `remoto`, NON `gira`.
	#
	# `gira`, qui sul portatile, fa girare **un secondo** di maglie: C10, C12,
	# C13.  ⛔ Le maglie che guardano il prodotto vogliono le scatole e la
	# scheda, che stanno sull'altra macchina — quindi un `pre-push` che chiama
	# `gira` e' un gancio che scatta, dice verde, e **non ha guardato il
	# prodotto**.  ⇒ E' la rete che muore in silenzio di §4.2, con l'aggravante
	# che il registro dice che sta girando.
	# ⭐ `remoto` decide qui e fa eseguire la'.
	# ═══════════════════════════════════════════════════════════════════
	if [ "$SOLO_QUI" = 1 ]; then
		AZIONE_GANCIO=gira
	else
		AZIONE_GANCIO=remoto
	fi
	{
		printf '#!/bin/sh\n'
		printf '# rete11 — installato da 11-gancio.sh il %s\n' "$(date -Is)"
		printf '# ⛔ Definito PER PERCORSO: e questo file non decide niente,\n'
		printf '#    passa la palla al gancio, che guarda i file cambiati.\n'
		printf 'exec bash %s %s --innesco %s\n' "$QUI/11-gancio.sh" "$AZIONE_GANCIO" "$QUALE"
	} > "$PERCORSO"
	chmod 755 "$PERCORSO"
	ok "gancio installato: $PERCORSO"
	inf "azione: $AZIONE_GANCIO"
	if [ "$SOLO_QUI" = 1 ]; then
		ko "⚠ ⛔ INSTALLATO A META': con «--solo-qui» questo gancio fa girare"
		inf '  solo C10 e il suo guasto innestato — [M] un secondo — e ⛔ NON'
		inf "  guarda il prodotto: le maglie del prodotto vogliono le scatole."
		inf "  ⇒ C12 dira' «il gancio e' vivo» e C13 «la rete sa dare rosso»,"
		inf "    ⛔ e tutt'e due diranno il vero avendo guardato un decimo della"
		inf "    rete.  ⚠ Si usa quando la macchina di prova non c'e', e si sa"
		inf "    che cosa si sta comprando"
	else
		inf "⇒ ⭐ decide qui (il deposito) ed esegue su $RETE11_REMOTA (le scatole)"
		inf "⇒ e adesso C12 puo' dire se e' vivo"
	fi
	;;

installato)
	CARTELLA=$(cartella_ganci)
	TROVATO=0
	for q in pre-commit pre-push; do
		D="$CARTELLA/$q"
		if [ -f "$D" ] && grep -q '11-gancio.sh' "$D" 2>/dev/null; then
			if [ -x "$D" ]; then ok "$q  ⇒  $D"; else ko "$q c'e' ma NON e' eseguibile: $D"; fi
			# ⛔⛔ E NON BASTA CHE IL GANCIO CI SIA: conta QUALE AZIONE chiama.
			#    `gira`, sul portatile, e' un secondo di maglie e NON guarda il
			#    prodotto.  ⇒ Un gancio installato cosi' scatta, dice verde, e
			#    non ha misurato niente delle scatole: e' la rete che muore in
			#    silenzio (§4.2) con il registro che dice che sta girando.
			#    ⚠ C12 questa distinzione non la fa — guarda che il file NOMINI
			#      il gancio.  ⇒ Finche' non la fa, la dice questa riga.
			if grep -q '11-gancio.sh remoto' "$D" 2>/dev/null; then
				inf "  ⭐ chiama «remoto»: decide qui, esegue sulle scatole"
			elif grep -q '11-gancio.sh gira' "$D" 2>/dev/null; then
				ko "  ⚠ chiama «gira»: qui gira solo la meta' del deposito"
				inf "    ⇒ le maglie del prodotto NON girano.  Per cablarle:"
				inf "      bash 11-gancio.sh installa $q"
			fi
			TROVATO=1
		fi
	done
	[ $TROVATO -eq 0 ] && ko "il gancio NON e' installato in $CARTELLA"
	printf '\n'
	if [ -f "$REGISTRO" ]; then
		inf "registro: $REGISTRO ($(grep -c . "$REGISTRO") righe)"
	else
		ko "⛔ nessun registro: il gancio non ha MAI girato"
	fi
	;;

registro)
	N=${1:-10}
	case "$N" in ''|*[!0-9]*) N=10 ;; esac
	[ -f "$REGISTRO" ] || { ko "nessun registro: il gancio non ha mai girato"; exit 1; }
	tail -n "$N" "$REGISTRO"
	;;

*)
	sed -n '2,14p' "$0"
	exit 2 ;;
esac
