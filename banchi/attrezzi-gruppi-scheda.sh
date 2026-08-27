#!/bin/bash
#
# attrezzi-gruppi-scheda.sh — ⭐ L'UNICO POSTO in cui un banco mette un
# inquilino nei gruppi della scheda, e ⭐ L'UNICO in cui VERIFICA che ci sia.
#
#   . banchi/attrezzi-gruppi-scheda.sh      # e poi: gruppi_scheda_dai_a UTENTE
#   bash banchi/attrezzi-gruppi-scheda.sh UTENTE        # come programma
#   bash banchi/attrezzi-gruppi-scheda.sh --testo       # ⭐ si STAMPA, per chi
#                                                       #   gira altrove
#
# ---------------------------------------------------------------------------
# ⛔⛔⭐ IL DIFETTO CHE QUESTO FILE CURA — «la sessione che nasce cieca»
#
# `fasi/10-multi-tenant-e-il-budget.md` §7.4: nessuna applicazione riesce ad
# aprire una finestra, zero fotogrammi, mai — `provanic4/5/6` su **98 · 55 · 50**
# tentativi.  Ha bloccato cinque prove della rete anti-regressione e rinviato
# una fase intera.
#
# ⭐ LA CAUSA, misurata sulla macchina vera il 27 agosto 2026: l'inquilino non
#    sta nei gruppi dei nodi `/dev/dri` (qui `video` e `render`).
#
#   | inquilini CON i due gruppi | `[M]` **17 su 17** vedono (1,92-2,10 s) |
#   | SENZA                      | `[M]` **0 su 4**, mai in 90 s, zero fotogrammi |
#   | ⭐ controprova             | dati i gruppi allo stesso inquilino ⇒ 2,04 s |
#
# ⛔⛔ E I BANCHI CREAVANO INQUILINI CIECHI PER CONTO LORO.  Un banco che misura
#    una sessione che non vede, credendola sana, e' PEGGIO di un banco che non
#    gira: scrive un numero e non dichiara di che prodotto sia.
#
# ⭐ PERCHE' UN FILE SOLO, E NON UNA RIGA IN OGNI TERRENO (`LEZIONI.md` §1.47):
#    dieci copie della stessa riga sono dieci posti da cui divergere, ed erano
#    gia' divergiti — `src/provisiona.sh` dava i gruppi, `attrezzi-utenti.sh`
#    no, e nessuno dei due lo diceva.
#
# ⛔ IL GRUPPO SI LEGGE DAL NODO, MAI DA UN NOME INCHIODATO.  `video` e `render`
#    sono i nomi di QUESTA distribuzione: dentro il chroot di `enter.sh` (che
#    ha `/dev` in rbind ma un `/etc/group` tutto suo) lo stesso gid puo' avere
#    un altro nome, o nessuno.  ⇒ si parte dal **gid** dello `stat`, e il nome
#    si CHIEDE a `getent`.
#
# ⚠ E SI SCORRONO TUTTI I NODI, non `renderD128`: `renderD128` e `renderD129`
#   si scambiano fra due avvii (lo dice gia' `src/provisiona.sh`), e `cardN` e
#   `renderDN` hanno gruppi DIVERSI che servono tutt'e due.
#
# ⭐ E LA VERIFICA CONFRONTA I NUMERI, non i nomi (E1, «scritto non e' in
#   vigore»): il vecchio `id -nG | grep -qw render` avrebbe detto OK su una
#   macchina dove il nodo appartiene a un altro gruppo.
# ---------------------------------------------------------------------------

# ═══ CORPO-INIZIO ═══  ⛔ Da qui a CORPO-FINE e' quel che `--testo` stampa:
#     niente qui dentro deve dipendere da questo file o da questa macchina.

# I gid dei nodi della scheda, uno per riga, senza doppioni.
gruppi_scheda_gid() {
	_gs_n=; _gs_g=
	for _gs_n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$_gs_n" ] || continue
		_gs_g=$(stat -c %g "$_gs_n" 2>/dev/null) || continue
		[ -n "$_gs_g" ] && printf '%s\n' "$_gs_g"
	done | sort -un
}

# Il nome di un gid, o vuoto se in /etc/group non ce n'e' uno.
gruppi_scheda_nome() { getent group "$1" 2>/dev/null | cut -d: -f1; }

# Quale nodo ha quel gid — serve solo a scrivere un messaggio che si capisce.
gruppi_scheda_nodo() {
	_gs_n=
	for _gs_n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$_gs_n" ] || continue
		[ "$(stat -c %g "$_gs_n" 2>/dev/null)" = "$1" ] && { printf '%s' "$_gs_n"; return 0; }
	done
	printf '/dev/dri'
}

# L'inquilino sta nel gruppo di quel gid?  ⭐ Si confrontano i NUMERI.
gruppi_scheda_ci_sta() {
	_gs_x=
	for _gs_x in $(id -G "$1" 2>/dev/null); do
		[ "$_gs_x" = "$2" ] && return 0
	done
	return 1
}

# I gid dei nodi che all'inquilino MANCANO, separati da spazio.
gruppi_scheda_mancanti() {
	_gs_g=; _gs_m=
	for _gs_g in $(gruppi_scheda_gid); do
		gruppi_scheda_ci_sta "$1" "$_gs_g" || _gs_m="${_gs_m:+$_gs_m }$_gs_g"
	done
	printf '%s' "$_gs_m"
}

# ⭐⭐ IL LAVORO: mette l'inquilino nei gruppi dei nodi e VERIFICA che ci sia.
#
#   0  ⭐ c'e' dentro davvero (o non c'e' niente da fare)
#   3  ⛔ NON c'e' dentro dopo il tentativo — chi chiama DEVE fermarsi
#   4  ⛔ i gruppi sono stati aggiunti ma il gestore d'utente era GIA' VIVO:
#         scritti si', in vigore no — chi chiama DEVE fermarsi
#   5  ⛔ un gid dei nodi non ha nessun nome in /etc/group
#
# ⛔ Non spegne niente da sola: `loginctl terminate-user` butta giu' anche il
#    figlio del server, e in fase 10/11 gli inquilini sono CONDIVISI fra banchi
#    che stanno misurando (I2).  ⇒ lo DICE, e si ferma.
gruppi_scheda_dai_a() {
	_gs_u=$1
	_gs_pref=${GRUPPI_SCHEDA_PREFISSO:-    }
	_gs_gid=$(gruppi_scheda_gid)

	if [ -z "$_gs_gid" ]; then
		printf '%s\033[1;31m⛔\033[0m  nessun nodo `cardN`/`renderDN` in /dev/dri: su questa\n' "$_gs_pref"
		printf '%s    macchina il compositore disegnera in SOFTWARE, e nessun gruppo\n' "$_gs_pref"
		printf '%s    puo rimediare.  ⚠ Il numero che questo banco misurera NON e\n' "$_gs_pref"
		printf '%s    quello del prodotto in hardware.\n' "$_gs_pref"
		return 0
	fi

	# 1. I nomi. ⛔ Un gid senza nome non si inventa e non si crea da qui.
	_gs_nomi=
	for _gs_g in $_gs_gid; do
		_gs_nome=$(gruppi_scheda_nome "$_gs_g")
		if [ -z "$_gs_nome" ]; then
			printf '%s\033[1;31m⛔⛔\033[0m il gid %s (di %s) NON ha nessun nome in /etc/group qui:\n' \
				"$_gs_pref" "$_gs_g" "$(gruppi_scheda_nodo "$_gs_g")"
			printf '%s    l inquilino «%s» non ci puo entrare, e la sua sessione NASCERA\n' "$_gs_pref" "$_gs_u"
			printf '%s    CIECA.  ⭐ La cura, da root: `groupadd -g %s scheda%s`\n' "$_gs_pref" "$_gs_g" "$_gs_g"
			return 5
		fi
		case " $_gs_nomi " in *" $_gs_nome "*) continue ;; esac
		_gs_nomi="${_gs_nomi:+$_gs_nomi }$_gs_nome"
	done

	# 2. Che cosa manca PRIMA — serve a sapere se stiamo cambiando qualcosa.
	_gs_prima=$(gruppi_scheda_mancanti "$_gs_u")

	if [ -n "$_gs_prima" ]; then
		# ⚠ `usermod -aG` vuole i nomi separati da virgola.
		_gs_virgole=$(printf '%s' "$_gs_nomi" | tr ' ' ',')
		usermod -aG "$_gs_virgole" "$_gs_u" || {
			printf '%s\033[1;31m⛔\033[0m  `usermod -aG %s %s` NON e riuscito\n' \
				"$_gs_pref" "$_gs_virgole" "$_gs_u"
			return 3; }
	fi

	# 3. ⭐ SI RILEGGE — E1: scritto non e' in vigore.
	_gs_dopo=$(gruppi_scheda_mancanti "$_gs_u")
	if [ -n "$_gs_dopo" ]; then
		for _gs_g in $_gs_dopo; do
			printf '%s\033[1;31m⛔⛔\033[0m «%s» NON E NEL GRUPPO DELLA SCHEDA «%s» (gid %s, il gruppo\n' \
				"$_gs_pref" "$_gs_u" "$(gruppi_scheda_nome "$_gs_g")" "$_gs_g"
			printf '%s    di %s)\n' "$_gs_pref" "$(gruppi_scheda_nodo "$_gs_g")"
		done
		printf '%s    ⛔ LA SUA SESSIONE NASCEREBBE E NON VEDREBBE NIENTE: zero fotogrammi,\n' "$_gs_pref"
		printf '%s    nessuna finestra si apre, e il ciclo gira in tondo fra «ZERO MONITOR»\n' "$_gs_pref"
		printf '%s    e «monitor virtuale montato» (fase 10 §7.4 — [M] 0 su 4 senza, 17 su 17 con).\n' "$_gs_pref"
		printf '%s    ⛔ QUESTO BANCO NON DEVE MISURARE: misurerebbe un prodotto che non esiste.\n' "$_gs_pref"
		return 3
	fi

	if [ -z "$_gs_prima" ]; then
		printf '%s\033[1;32mOK\033[0m  ⭐ «%s» era gia nei gruppi dei nodi della scheda (%s): la sua\n' \
			"$_gs_pref" "$_gs_u" "$_gs_nomi"
		printf '%s    sessione puo vedere in hardware\n' "$_gs_pref"
		return 0
	fi

	printf '%s\033[1;32mOK\033[0m  ⭐ «%s» messo nei gruppi LETTI DAI NODI: %s (gid %s)\n' \
		"$_gs_pref" "$_gs_u" "$_gs_nomi" "$(printf '%s' "$_gs_gid" | tr '\n' ' ')"

	# 4. ⛔⛔ SCRITTI SI', IN VIGORE NO — e questo e' il caso che inganna.
	#    I gruppi arrivano al compositore solo quando RINASCE il gestore
	#    d'utente: se ce n'era gia' uno vivo, la sessione che sta girando e'
	#    ancora cieca, e un banco che misurasse adesso misurerebbe il buio.
	if pgrep -u "$_gs_u" >/dev/null 2>&1; then
		printf '%s\033[1;31m⛔⛔\033[0m i gruppi sono stati AGGIUNTI ADESSO, ma «%s» aveva gia dei\n' \
			"$_gs_pref" "$_gs_u"
		printf '%s    processi vivi: un processo tiene i gruppi che aveva quando e NATO.\n' "$_gs_pref"
		printf '%s    ⇒ La sessione che sta girando e ANCORA CIECA.\n' "$_gs_pref"
		printf '%s    ⭐ La cura, da root, e poi si rifa questo passo:\n' "$_gs_pref"
		printf '%s        loginctl terminate-user %s\n' "$_gs_pref" "$_gs_u"
		printf '%s    ⚠ NON lo faccio io: butterebbe giu anche la sessione di un altro banco (I2).\n' "$_gs_pref"
		return 4
	fi
	return 0
}
# ═══ CORPO-FINE ═══

# ---------------------------------------------------------------------------
# ⭐ COME PROGRAMMA — e ⭐ `--testo`, che e' quel che tiene UNO il posto della
#    cura anche per chi non puo' fare `.` su questo file:
#
#   · `banchi/attrezzi-utenti.sh` manda i comandi DENTRO il chroot con
#     `enter.sh --root "…"`, e li' dentro questo file non c'e';
#   · `banchi/07-b63-terreno.sh` spedisce un copione alla macchina di prova.
#
#   ⚠ Il testo si infila in una stringa gia' espansa (`"$TESTO"`, `$(cat …)`):
#     la shell NON riespande il risultato di un'espansione, quindi i `$` che
#     stanno qui dentro arrivano di la' intatti.
# ---------------------------------------------------------------------------
# ⚠ Il controllo sul nome di `$0` distingue «eseguito» da «sorgente con `.`»:
#   quando un terreno fa `. attrezzi-gruppi-scheda.sh`, `$0` resta il nome del
#   TERRENO, e qui sotto non succede niente — nemmeno se il terreno era stato
#   chiamato lui con un argomento.
if [ "$(basename "$0")" = "attrezzi-gruppi-scheda.sh" ]; then
	case "${1:-}" in
	--testo)
		sed -n '/^# ═══ CORPO-INIZIO/,/^# ═══ CORPO-FINE/p' "$0"
		exit 0 ;;
	"")
		printf 'uso: bash %s UTENTE   |   bash %s --testo\n' "$0" "$0"
		exit 2 ;;
	*)
		[ "$(id -u)" -eq 0 ] || { printf '    ⛔ va lanciato DA ROOT\n'; exit 2; }
		gruppi_scheda_dai_a "$1"
		exit $? ;;
	esac
fi
