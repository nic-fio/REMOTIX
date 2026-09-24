#!/bin/bash
# ===========================================================================
# 11-capacita-del-prodotto.sh — ⭐⭐ CHE COSA IL PRODOTTO SA FARE, E SU QUALE
#                                DESKTOP: la lista, in un posto solo
# ===========================================================================
#
# ⛔ Non si esegue: si LEGGE (`source`) da `11-gancio.sh` e da `11-accendi.sh`.
#
# ⛔⛔ PERCHE' ESISTE — 21 settembre 2026, fase 13, incremento 2.
#   Fino a oggi il «su quale desktop gira questa maglia» era scritto DUE volte,
#   a mano, in due whitelist: `le_cinque_nuove` in `11-gancio.sh` (tutte le
#   maglie del prodotto) e il ramo `c8b` di `11-accendi.sh` (solo C8b).
#   ⇒ `fasi/13-xfce.md`, «Il banco», punti 1 e 2: due posti da aprire, e
#     aprendone uno solo C8b(xfce) restava muta a 3 senza che niente lo dicesse
#     (`LEZIONI.md` §1.46 — due elenchi identici sono due elenchi che il giorno
#     dopo non lo sono piu').
#   ⚠ E il cancello diceva UNA ragione per tutte: *«il prodotto sa avviare solo
#     GNOME e KDE»*.  Da quando XFCE nasce e si vede (C1(xfce) verde) quella
#     frase e' FALSA, e le maglie che guardano pixel possono giudicare mentre
#     quelle che vogliono l'input ancora no.  ⇒ Il cancello deve saper dire
#     **per quale capacita'** salta.
#
# ⭐ LA FORMA: due tavole piccole.
#   1. che cosa ogni DESKTOP ha dal prodotto  (`capacita_del_desktop`)
#   2. che cosa ogni MAGLIA vuole              (`capacita_della_maglia`)
#   Una maglia gira se il desktop ha TUTTO quel che lei vuole; altrimenti salta
#   dicendo la PRIMA capacita' che manca, e perche' (`perche_manca`); la
#   domanda si fa con `prodotto_pronto`.
#
# ⛔⛔ E QUI NON SI DECIDE NESSUN METRO.  Aprire una capacita' non ammorbidisce
#     niente: vuol dire soltanto che la maglia GUARDA, col suo metro di sempre.
#     ⇒ Una capacita' si aggiunge qui NELL'INCREMENTO in cui il prodotto la da'
#       (`fasi/13-xfce.md`, «Gli incrementi»), non prima: un 3 che si ripete
#       per una decisione presa apposta e' il cugino del rosso perpetuo (§1.49).
#
# ⚠ Un desktop che NON sta qui non ha nessuna capacita': tutte le maglie del
#   prodotto saltano, e la ragione e' quella vera — il prodotto non lo
#   riconosce.  ⇒ Il default e' CHIUSO: un desktop nuovo (la famiglia
#   `desktop-nuovo`) non gira niente finche' qualcuno non lo scrive qui.
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. ⭐ I DESKTOP CHE IL PRODOTTO SA ACCENDERE, e che cosa ne sa fare.
#
#   immagine   la cattura arriva al cliente     (C1 verde su quella scatola)
#   forma      la forma vera del puntatore       (C21 verde; fase 14: su gnome
#              c'era gia', kde/xfce/lxqt si aprono quando C21 e' verde li')
#   input      tastiera e mouse arrivano         (C4 verde)
#   appunti    gli appunti nei due versi         (C17 verde)
#
# ⚠ `[M]` gnome e kde: tutte e tre — la rete del 20 set 2026 le ha verdi coi
#   loro guasti visti (`fasi/13-xfce.md`, la baseline).
# ⭐ xfce: SOLO l'immagine — fase 13, incremento 2 (21 set 2026, C1(xfce)
#   verde).  L'input e' l'incremento 3, gli appunti il 5.
# ⭐⭐ E DAL 21 SETTEMBRE 2026, MATTINA, ANCHE L'INPUT E GLI APPUNTI — aperti
#     solo DOPO la misura, non prima: `[M]` binario `0c0634dd`, scatola xfce
#     rifatta da zero, lanciate a mano con `11-accendi.sh`:
#       C4(xfce)  VERDE · guasti `--senza-tasto` e `--scena-sorda` VISTI
#       C6(xfce)  VERDE · guasto `--uccidi-la-sessione` VISTO
#       C17(xfce) VERDE (A · B · R, arbitro wl-clipboard) · `--senza-copia` VISTO
#     ⛔ Una capacità si apre qui quando la maglia che la giudica ha dato VERDE
#        e ha visto il suo guasto — non quando il codice c'è.
# ⭐ lxqt: TUTTE E TRE dal 24 settembre 2026 — fase 14 (`fasi/14-lxqt.md`).  Fino
#   ad allora NIENTE: il prodotto diceva «NESSUN DESKTOP RICONOSCIUTO».  Aperte
#   solo DOPO la misura, `[M]` sulla scatola di sviluppo `rete14-lxqt` (binari
#   `404f9907` → `1a10a66e`), lanciate a mano con `11-accendi.sh`:
#     C1(lxqt)×3 VERDE · C2 C3 C4 C6 C8b C17 C20 VERDI · 16 guasti su 16 VISTI
#     (`--senza-tasto` `--scena-sorda` `--uccidi-la-sessione` `--senza-copia` …)
# ---------------------------------------------------------------------------
DESKTOP_COL_PRODOTTO="gnome kde xfce lxqt"

capacita_del_desktop() {
	case "$1" in
	gnome) printf 'immagine input appunti forma' ;;
	kde)   printf 'immagine input appunti forma' ;;
	xfce)  printf 'immagine input appunti forma' ;;
	lxqt)  printf 'immagine input appunti forma' ;;
	*)     printf '' ;;
	esac
}

# ---------------------------------------------------------------------------
# 2. ⭐ CHE COSA OGNI MAGLIA VUOLE DAL PRODOTTO.
#
# ⛔ Solo le maglie che il cancello governa.  C1, C5, C7, C8, C9 e il passo 0
#   non passano da qui: girano su ogni scatola da sempre, e dicono da sole
#   «non ho potuto guardare» — ⛔ toglierle dal giro sarebbe un'altra decisione,
#   non questa.
#
#   C2   una finestra si apre           guarda il PIXEL          ⇒ immagine
#   C3   i fotogrammi cambiano          guarda il PIXEL          ⇒ immagine
#   C8b  la pagina si vede dal cliente  guarda il PIXEL          ⇒ immagine
#   C4   il tasto arriva allo schermo   manda un TASTO           ⇒ + input
#   C6   si stacca e si ritrova         ⚠ vedi sotto             ⇒ + input
#   C17  gli appunti nei due versi      il fuoco col CLIC del cliente
#                                       (`--clic`) e gli appunti ⇒ + input + appunti
#   C20  la rinascita dopo «Esci»       guarda il PIXEL          ⇒ immagine
#
# ⚠⚠ C20 E IL GESTO «ESCI» — dichiarato, perche' NON e' una capacita' del
#   prodotto.  Uscire dal menu e' un gesto del DESKTOP (`org.kde.Shutdown`,
#   `org.gnome.SessionManager`, `xfce4-session-logout`), e la maglia se lo
#   cerca da se' con la stessa domanda che fa `src/sessione.c` — se in quella
#   scatola non c'e' nessuno dei tre, dice **3** e spiega quale manca.
#   ⛔ Non si mette qui una capacita' «uscita»: qui ci va quel che il PRODOTTO
#     da', e il prodotto non da' il menu.  Quel che il prodotto deve dare e'
#     accorgersi che la sessione e' finita — e senza immagine non si potrebbe
#     comunque giudicare la sessione che rinasce.
#
# ⛔ C19 NON sta qui: non chiede niente al prodotto.  Guarda la SCATOLA (chi e'
#   rimasto dentro), e la scatola c'e' su ogni desktop — come C1, C5, C7, C9,
#   C18.  ⇒ Metterci un cancello vorrebbe dire non guardare lo sporco proprio
#   sui desktop dove il prodotto fa meno, che e' il contrario di quel che serve.
#
# ⚠⚠ C6 E L'INPUT — dichiarato, perche' NON l'ho letto nel codice.
#   `[R]` 21 set 2026: il cliente di C6 (`attacca`) non manda ne' tasti ne'
#   clic, e la scena la accende il banco dentro la sessione (`apri_la_scena`).
#   ⇒ La dipendenza scritta qui e' quella del PIANO (`fasi/13-xfce.md`, tabella
#     degli incrementi: *«3 · … C4(xfce), e C3 · C6 su xfce»*), non una lettura
#     della maglia.  ⛔ Prima di aprire C6(xfce) si decide se il piano ha una
#     ragione che il codice non mostra; se non ce l'ha, C6 vuole solo
#     l'immagine e la si sposta nella riga sopra.
# ---------------------------------------------------------------------------
capacita_della_maglia() {
	case "$1" in
	C2|C3|C8b|C20) printf 'immagine' ;;
	C4|C6|C22|C23) printf 'immagine input' ;;
	C17)       printf 'immagine input appunti' ;;
	C21)       printf 'immagine input forma' ;;
	# ⛔ Una maglia che non conosco non e' «libera»: vuole una capacita' che
	#   nessun desktop ha, e cosi' salta dicendolo invece di girare a caso.
	*)         printf 'sconosciuta' ;;
	esac
}

# ---------------------------------------------------------------------------
# 3. ⭐ LA RAGIONE, scritta per chi legge il registro.
# ---------------------------------------------------------------------------
perche_manca() {
	local desktop=$1 capacita=$2
	case " $DESKTOP_COL_PRODOTTO " in
	*" $desktop "*) : ;;
	*)
		printf 'il prodotto non riconosce il desktop «%s» (src/sessione.c, sessione_desktop: «NESSUN DESKTOP RICONOSCIUTO»)' "$desktop"
		return
		;;
	esac
	case "$desktop:$capacita" in
	xfce:input)
		printf 'l input su XFCE e l incremento 3 della fase 13 (virtual-keyboard, virtual-pointer: fasi/13-xfce.md)' ;;
	xfce:appunti)
		printf 'gli appunti su XFCE sono l incremento 5 della fase 13 (fasi/13-xfce.md)' ;;
	*:forma)
		printf 'la forma vera del puntatore non arriva al browser su %s (C21, fase 14)' "$desktop" ;;
	*:sconosciuta)
		printf 'la maglia non e dichiarata in 11-capacita-del-prodotto.sh: non so che cosa vuole' ;;
	*)
		printf 'il prodotto non da «%s» su %s (11-capacita-del-prodotto.sh)' "$capacita" "$desktop" ;;
	esac
}

# ---------------------------------------------------------------------------
# ⭐ LA DOMANDA DEL CANCELLO: `prodotto_pronto <maglia> <desktop>`
#
#   torna 0 in silenzio            se c'e' tutto    ⇒ la maglia gira
#   torna 1 e STAMPA LA RAGIONE    se manca qualcosa ⇒ la maglia salta
#
# ⛔⛔ E IL VERSO NON E' UNA QUESTIONE DI GUSTO.  Il chiamante scrive
#     `if ! perche=$(prodotto_pronto …); then salta …; else gira …`, e ⇒ SOLO
#     lo 0 fa girare.  Se questa funzione non ci fosse (file non letto, nome
#     sbagliato) il guscio uscirebbe 127, ⭐ e 127 SALTA.  `[M]` 21 set 2026:
#     col verso opposto («manca? 0 = si'») la prima stesura, senza la lista,
#     faceva girare TUTTO in silenzio — un cancello che si apre quando si rompe.
# ---------------------------------------------------------------------------
prodotto_pronto() {
	local maglia=$1 desktop=$2 c ha detto=""
	ha=" $(capacita_del_desktop "$desktop") "
	# ⭐ Si dicono TUTTE le capacita' che mancano, non la prima: C17 su xfce
	#   aspetta l'input E gli appunti, e chi legge il registro deve saperlo.
	#   ⚠ Un desktop che il prodotto non riconosce ha una ragione sola.
	for c in $(capacita_della_maglia "$maglia"); do
		case "$ha" in
		*" $c "*) : ;;
		*)
			case " $DESKTOP_COL_PRODOTTO " in
			*" $desktop "*) : ;;
			*) perche_manca "$desktop" "$c"; return 1 ;;
			esac
			[ -n "$detto" ] && detto="$detto · "
			detto="$detto$(perche_manca "$desktop" "$c")"
			;;
		esac
	done
	[ -z "$detto" ] && return 0
	printf '%s' "$detto"
	return 1
}
