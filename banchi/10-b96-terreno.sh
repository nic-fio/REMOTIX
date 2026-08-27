#!/usr/bin/env bash
# ===========================================================================
# 10-b96-terreno — il terreno del banco DEL REGISTRO A PIU' SESSIONI (B5)
#
#   porta 8150 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6`
#   (1105) e ⭐ `provamt1` (1110), che e' CONDIVISO
#   albero /media/REMOTIX/src/10b5-src · lavoro /media/REMOTIX/tmp/10b5
#   unita' remotix-8150 · ban-file, socket e certificati suoi
#
# ===========================================================================
# ⛔ CHE COSA NON RISCRIVE — e' la regola di `09-b86-terreno.sh`
# ===========================================================================
#
# Tutto quel che riguarda **un** utente e **il** server sta gia' scritto e gia'
# certificato in `banchi/07-b64-terreno.sh`: la parola d'ordine che non passa da
# `argv` (D12), i gruppi `render,video`, `enable-linger`, il controllo `ldd` su
# ngtcp2/nghttp3 prima di accendere, l'unita' di sistema invece di un `setsid`,
# la lettura dei limiti DOPO l'`exec`.  ⇒ Qui non se ne riscrive una riga: si
# esporta il PROPRIO ambiente e si CHIAMA quello.
#
# ⭐ Questo file aggiunge solo quel che nasce dall'avere PIU' utenti: il ciclo
#    che li provvede, lo `stato` che smaschera i palchi orfani, e lo `sgombra`
#    che chiude i palchi lasciando in piedi il fondo di `linger`.
#
# ===========================================================================
# ⛔⛔ `provamt1` E' DI TUTTI — e per questo la sua parola NON si cambia
# ===========================================================================
#
# Il preambolo del giro 2 dice che `provamt1…provamt11` sono **condivisi**.  Per
# questa misura ne serve **uno solo** (i miei sono tre, e le sessioni devono
# essere almeno quattro di utenti diversi).
#
# ⛔ `10-b91-terreno-dieci.sh` pone a quegli utenti la parola `mt-dieci-2026`.
#    Se io ne ponessi un'altra, il banco di un altro agente che gira nello
#    stesso pomeriggio si sentirebbe rispondere `CREDENZIALI_ERRATE` — e non
#    saprebbe perche'.  ⇒ ⭐ **La parola di TUTTI E QUATTRO e' `mt-dieci-2026`**:
#    per i tre miei e' una scelta libera, per `provamt1` e' la sua, riscritta
#    identica.  ⚠ E' l'unico modo che ho di provvedere quattro utenti con un
#    file `parola` solo senza togliere niente a nessuno.
#
# ⛔ E il protocollo del preambolo del giro 2 vale per intero: **lucchetto della
#    GPU prima**, `stato` per i palchi orfani, `sgombra` alla fine.
#
# ===========================================================================
# ⛔ L'ISOLAMENTO
# ===========================================================================
#
# ⛔⛔ NON SI TOCCANO: nessuna porta che non sia la **8150**, nessun utente che
#      non sia nella lista qui sotto, nessuna unita' che non sia `remotix-8150`.
#      Il ban di `RCP.md` §4.4-bis e' per INDIRIZZO e dura 12 ore: partiamo
#      tutti dallo stesso indirizzo, e chi lo fa scattare mette fuori uso ogni
#      altro agente.  Si sblocca con `sblocca`, sul PROPRIO socket.
# ⛔ Nessun `netem`: questo banco non tocca la rete di nessuno.
#
# Uso (dal portatile):
#     bash banchi/10-b96-terreno.sh porta      # sorgenti + compila
#     bash banchi/10-b96-terreno.sh utenti
#     bash banchi/10-b96-terreno.sh accendi
#     bash banchi/10-b96-terreno.sh stato
#     bash banchi/10-b96-terreno.sh sgombra
#     bash banchi/10-b96-terreno.sh spegni
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8150}
# ⛔⛔ LA PAROLA DEGLI UTENTI CONDIVISI E' UNA SOLA, E NON E' QUESTA — 25 ago 2026.
#
#   Questo copione dichiarava `mt-dieci-2026` **e la riposava a ogni giro**, e
#   fintanto che ogni terreno riscriveva la parola l'ultimo che chiamava
#   vinceva: sembrava che funzionasse.
#
#   ⛔ Dal 25 agosto il terreno **non rifa' piu' la parola a un utente che
#     esiste gia'** (era la cura di un difetto peggiore: l'ultimo che chiamava
#     buttava fuori tutti gli altri).  ⇒ Da allora vale **una parola sola**, ed
#     e' quella con cui `provadec4/5/6` sono stati creati: `dec-pieno-2026`.
#
#   `[M]` Con `mt-dieci-2026` `provadec4` risponde `CONGEDO 0x07` su una
#   macchina sana — e ⛔⛔ **ogni respinto brucia uno dei TRE tentativi del ban
#   per INDIRIZZO, che dura DODICI ORE e mette fuori uso ogni altro banco.**
#
# ⚠ `provamt1` ha la sua (`mt-dieci-2026`): chi mescola le due famiglie passa
#   `PAROLA_UTENTE=` a mano, per utente, invece di dichiararne una per tutti.
export PAROLA_UTENTE=${PAROLA_UTENTE:-dec-pieno-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b5-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b5}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b5-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b5}
export UNITA=${UNITA:-remotix-$PORTA}

# ⭐ I QUATTRO, nome e uid nella stessa riga: due tabelle in due posti divergono.
#    ⚠ `provamt1` e' l'ultimo apposta — cosi' `QUANTI=3` esclude il condiviso.
UTENTI_TUTTI="provadec4:1103 provadec5:1104 provadec6:1105 provamt1:1110"
QUANTI=${QUANTI:-4}
UTENTI=$(echo "$UTENTI_TUTTI" | tr ' ' '\n' | head -n "$QUANTI" | tr '\n' ' ')

# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, e non si toccano mai.
VICINE=${VICINE:-"7700 7730 8100 8110 8120 8130 8140 8160 8170 8180 8190"}

QUI=$(cd "$(dirname "$0")/.." && pwd)
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SULLA MACCHINA DI PROVA, DA ROOT
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--sul-server" ]; then
	PASSO=${2:-stato}
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--sul-server» va eseguito DA ROOT"; exit 2; }
	mkdir -p "$LAV" 2>/dev/null

	# ⛔⛔ IL PALCO ORFANO — la stessa lista di `10-b91-terreno-dieci.sh`.
	#     Non e' «tutti i processi dell'uid»: `enable-linger` ne fa nascere
	#     `[M]` sette per utente apposta, e chiamarli orfani vorrebbe dire
	#     sgomberare proprio quel che il terreno esiste per tenere in piedi.
	PALCO='gnome-shell|gnome-session|gnome-settings|mutter|Xwayland|dconf|04-b30-scena|remotix-figlio|ssh-agent|at-spi|gvfs|gjs|goa-|tracker|evolution|xdg-|gsd-|gcr-'

	case "$PASSO" in
	stato)
		R=""
		for p in $VICINE; do
			R="$R$p:$(ss -uln 2>/dev/null | grep -c ":$p ") "
		done
		printf '    --  ascoltatori NON miei (si contano, non si toccano): %s\n' "$R"
		printf '    --  il mio server sulla %s: %s ascoltatore/i · unita\047 %s\n' \
			"$PORTA" "$(ss -uln 2>/dev/null | grep -c ":$PORTA ")" \
			"$(systemctl is-active "$UNITA.service" 2>/dev/null)"
		printf '    --  carico: %s\n' "$(uptime | sed 's/.*average/media/')"
		guai=0
		for uu in $UTENTI; do
			u=${uu%%:*}; n=${uu##*:}
			riga=""
			if id "$u" >/dev/null 2>&1; then riga="$riga utente=si"; else riga="$riga utente=NO"; guai=$((guai+1)); fi
			# ⛔ Uno stato che non si legge NON e' «linger spento» (`CODER.md` §3.10).
			ling=$(loginctl show-user "$u" -p Linger --value 2>&1)
			case "$ling" in
			yes) riga="$riga linger=si" ;;
			no)  riga="$riga linger=NO"; guai=$((guai+1)) ;;
			*)   riga="$riga linger=??«$(echo "$ling" | head -1 | cut -c1-30)»"; guai=$((guai+1)) ;;
			esac
			if [ -d "/run/user/$n" ]; then riga="$riga run=si"; else riga="$riga run=NO"; guai=$((guai+1)); fi
			gr=$(id -nG "$u" 2>/dev/null || echo "-")
			case " $gr " in *" render "*) case " $gr " in *" video "*) riga="$riga gruppi=si" ;;
				*) riga="$riga gruppi=NO(video)"; guai=$((guai+1)) ;; esac ;;
			*) riga="$riga gruppi=NO(render)"; guai=$((guai+1)) ;; esac
			palco=$(pgrep -u "$n" -a 2>/dev/null | grep -cE "$PALCO" || true)
			# ⚠ `pgrep -c` stampa 0 ED ESCE 1: un `|| echo 0` in coda
			#   stamperebbe DUE zeri e la riga direbbe «00 processi».
			tutti=$(pgrep -u "$n" -c 2>/dev/null); [ -z "$tutti" ] && tutti=0
			if [ "$palco" != "0" ]; then
				riga="$riga ⛔PALCO-ORFANO=$palco (processi in tutto: $tutti)"
				guai=$((guai+1))
			else
				riga="$riga palco=pulito (fondo linger: $tutti processi)"
			fi
			printf '    --  %-10s uid %-5s %s\n' "$u" "$n" "$riga"
		done
		if [ "$guai" = 0 ]; then
			ok "i $QUANTI utenti ci sono, hanno linger e gruppi, e non c'e' nessun palco orfano"
			exit 0
		fi
		ko "⛔ $guai cose non tornano sul terreno: NON si misura cosi'"
		exit 2 ;;

	sgombra)
		log "Sgombro i MIEI palchi e i MIEI clienti"
		inf "⭐ il fondo di «enable-linger» resta in piedi APPOSTA: ammazzarlo"
		inf "   vorrebbe dire far misurare al giro dopo la sua RINASCITA"
		for uu in $UTENTI; do
			n=${uu##*:}
			pkill -u "$n" -f -- "$PALCO" 2>/dev/null
		done
		# ⚠ I clienti girano da root dentro il contenitore: si riconoscono dal
		#   file del giornale, che porta il MIO lavoro nel nome.  ⛔ E la classe
		#   di caratteri `[/]` non e' un vezzo: senza, `pkill -f` combacia con la
		#   PROPRIA riga di comando e lascia la pulizia a meta' in silenzio.
		pkill -f -- "--giornale [/]srv/remotix/tmp/10b5/" 2>/dev/null
		pkill -f "10-b92-cliente[.]py --cliente" 2>/dev/null
		sleep 3
		resti=0
		for uu in $UTENTI; do
			n=${uu##*:}
			c=$(pgrep -u "$n" -a 2>/dev/null | grep -cE "$PALCO" || true)
			[ "$c" != "0" ] && { dub "uid $n ha ancora $c processi del palco: mando -9"; pkill -9 -u "$n" -f -- "$PALCO" 2>/dev/null; resti=$((resti+1)); }
		done
		sleep 1
		ok "sgomberato (con $resti insistenze)"
		exit 0 ;;

	orologio)
		python3 -c 'import time; print("%.3f" % (time.clock_gettime(time.CLOCK_MONOTONIC)*1000))'
		exit 0 ;;

	*)
		ko "passo sconosciuto sul server: $PASSO"; exit 2 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE
# ═══════════════════════════════════════════════════════════════════════════
SUL_SERVER="bash $ALBERO/banchi/$(basename "$0") --sul-server"

# ⛔ Un solo `sudo`, e la catena dentro la SUA shell: un `<` o un `|` in coda
#    ruberebbe lo stdin a `sudo -S`, che allora non legge piu' la parola.
remoto() { ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $1 $SUL_SERVER $2"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti DELL'ALBERO DI LAVORO in $ALBERO"
	printf '    --  HEAD = %s (⚠ e NON e" quel che spedisco)\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)"
	for f in registro.c registro.h webtransport.c figlio.c rcp.c codificatore.c; do
		inf "md5 locale $f: $(md5sum "$QUI/src/$f" | cut -d' ' -f1)"
	done
	# ⛔ Le due copie di rcp.c/rcp.h/autenticazione.c si controllano QUI:
	#    `src/costruisci.sh` si rifiuta di compilare se divergono (R12.3), e un
	#    rifiuto a 200 km costa un giro di ssh per dire una cosa che si sa gia'.
	for f in rcp.c rcp.h autenticazione.c; do
		if ! cmp -s "$QUI/src/$f" "$QUI/banchi/rcp/$f"; then
			ko "⛔ src/$f e banchi/rcp/$f DIVERGONO: la costruzione fallirebbe (R12.3)"
			exit 2
		fi
	done
	ok "le due copie di rcp.c/rcp.h/autenticazione.c sono allineate"
	# ⛔ Si escludono `*.o` e `src/remotix`: spedendoli, `make` troverebbe tutto
	#    aggiornato e resterebbe il binario del PORTATILE — la forma D5.
	tar -C "$QUI" --exclude='src/remotix' --exclude='src/*.o' -cf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py \
		banchi/10-b96-terreno.sh banchi/10-b96-registro.py | \
		gzip | ssh -o BatchMode=yes "$MACCHINA" \
		"mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
		ko "⛔ i sorgenti non sono arrivati"; exit 2; }
	ok "sorgenti in $ALBERO"

	log "2 · Compilo dentro il contenitore sulla macchina di prova"
	if ! ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ la compilazione e' fallita: NON accendo niente"
		exit 2
	fi
	ok "compilato"

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO — si dichiara l'md5.
	#     ⭐ E si rileggono dai sorgenti SPEDITI le quattro righe che questo
	#     banco esiste per misurare: il formato del registro, il gancio che
	#     butta il contesto, l'area unica dei figli.
	log "3 · ⛔ CHE COSA HO COSTRUITO — e le righe del difetto R10-A4"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario:    \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 registro.c: \\\$(md5sum $ALBERO/src/registro.c | cut -d' ' -f1)
		 grep -n 'snprintf(buf, sizeof buf' $ALBERO/src/registro.c
		 grep -n -A2 'static void gancio_registra' $ALBERO/src/webtransport.c
		 grep -n 'define REG_FIGLIO' $ALBERO/src/figlio.h\"" \
		|| { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

utenti)
	log "I $QUANTI utenti — ⛔ ciascuno delegato a 07-b64-terreno.sh, che e' certificato"
	inf "⛔ D12: la parola d'ordine NON passa da argv — file 0600 e chpasswd dallo stdin"
	inf "⛔ gruppi render,video e enable-linger per ciascuno, o il desktop non parte"
	inf "⚠ la parola e' «$PAROLA_UTENTE» — quella di provadec4/5/6; ⛔ provamt1 ha la SUA"
	inf "  che e' condiviso — riscriverla identica non toglie niente a nessuno"
	for uu in $UTENTI; do
		u=${uu%%:*}; n=${uu##*:}
		printf '\n  ── %s (uid %s) ──\n' "$u" "$n"
		if ! UTENTE="$u" UID_B="$n" bash "$QUI/banchi/07-b64-terreno.sh" utente; then
			ko "⛔ «$u» non si e' provvisto: mi fermo QUI"
			exit 2
		fi
	done
	ok "$QUANTI utenti provvisti · la parola sta in $LAV/parola (0600), uguale per tutti"
	exec "$0" stato ;;

stato)    remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA QUANTI=$QUANTI VICINE='$VICINE'" stato ;;
sgombra)  remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA QUANTI=$QUANTI" sgombra ;;
orologio) remoto "LAV=$LAV" orologio ;;
accendi|spegni|sblocca)
	# ⛔ Non se ne riscrive una riga: il MIO ambiente, e il file certificato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
*)
	ko "passo sconosciuto: $PASSO"
	sed -n '/^# Uso (dal portatile)/,/^# ===/p' "$0"
	exit 2 ;;
esac
