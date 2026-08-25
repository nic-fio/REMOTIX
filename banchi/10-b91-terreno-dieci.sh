#!/usr/bin/env bash
# ===========================================================================
# 10-b91-terreno-dieci — IL TERRENO DI DIECI UTENTI VERI, e di UN SOLO server.
#
#   porta 8100 · utenti `provamt1` … `provamt10` (uid 1110-1119)
#   ⭐ e `provamt11` (uid 1120) SOLO per la domanda dell'UNDICESIMO
#   albero /media/REMOTIX/src/10a6-src · lavoro /media/REMOTIX/tmp/10a6
#   unita' remotix-8100 · ban-file, socket e certificati suoi
#
# ===========================================================================
# ⛔ CHE COSA NON RISCRIVE — e non e' pigrizia, e' la regola di 09-b86
# ===========================================================================
#
# Tutto quel che riguarda **un** utente e **il** server e' gia' scritto e gia'
# certificato in `banchi/07-b64-terreno.sh`: la parola d'ordine che non passa
# da `argv` (D12), i gruppi `render,video`, `enable-linger`, il controllo
# `ldd` su ngtcp2/nghttp3 prima di accendere, l'unita' di sistema invece di un
# `setsid`, la lettura dei limiti DOPO l'`exec`.  ⇒ Qui non se ne riscrive una
# riga: si esporta il PROPRIO ambiente e si CHIAMA quello.
#
# ⭐ Questo file aggiunge le tre cose che nascono dal **numero dieci**:
#
#   1. `utenti`      — il ciclo che provvede i dieci, uno per uno, delegando
#                      ogni singolo utente a `07-b64-terreno.sh utente`;
#   2. `stato`       — ⛔ per CIASCUNO dei dieci: c'e', linger acceso,
#                      `/run/user/<uid>` esiste, e **nessun palco orfano**;
#   3. `uno-per-volta` — ⛔⛔ la verifica che vale piu' di tutte: ciascuno dei
#                      dieci arriva a `SESSIONE` **da solo**, PRIMA di provarli
#                      insieme.  Senza, un rosso della salita non si sa se e'
#                      del numero dieci o del quinto utente provvisto male.
#
# ===========================================================================
# ⛔⛔ IL PALCO ORFANO — la ragione per cui `stato` guarda i processi
# ===========================================================================
#
# `LEZIONI.md` §1.29 e la fase 9: un palco rimasto in piedi dal giro precedente
# **non da' rosso, da' un numero plausibile**.  Un `gnome-shell` di `provamt3`
# ancora vivo quando la salita comincia vuol dire che al gradino 3 non nasce
# niente — la sessione si riattacca al palco vecchio (invariante I4, ed e'
# giusto cosi') — e i millisecondi dell'apertura, la memoria e l'occupazione
# della GPU di quel gradino sono quelli di un altro giro.  ⇒ Si guarda **prima**
# di misurare, e si dice chi c'e'.
#
# ===========================================================================
# ⛔ L'ISOLAMENTO
# ===========================================================================
#
# ⛔⛔ NON SI TOCCANO: gli utenti `prova`, `prova2`, `provanr*`, `provar7`,
#      `provan9`, `provadec*`, e nessuna porta che non sia la **8100**.
#      Il ban di `RCP.md` §4.4-bis e' per INDIRIZZO e dura 12 ore: partiamo
#      tutti dallo stesso indirizzo, e chi lo fa scattare mette fuori uso ogni
#      altro agente.  Si sblocca con `sblocca`, sul PROPRIO socket.
# ⛔ Nessun `netem`: questo banco non tocca la rete di nessuno.
#
# Uso (dal portatile):
#     bash banchi/10-b91-terreno-dieci.sh porta          # sorgenti + compila
#     bash banchi/10-b91-terreno-dieci.sh utenti         # i dieci (+ l'undicesimo)
#     bash banchi/10-b91-terreno-dieci.sh accendi
#     bash banchi/10-b91-terreno-dieci.sh stato
#     bash banchi/10-b91-terreno-dieci.sh uno-per-volta  # ⛔ prima della salita
#     bash banchi/10-b91-terreno-dieci.sh sblocca
#     bash banchi/10-b91-terreno-dieci.sh spegni
#     bash banchi/10-b91-terreno-dieci.sh sgombra        # ⛔ chiude palchi e clienti MIEI
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export MACCHINA PAROLA_SUDO
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8100}
export PAROLA_UTENTE=${PAROLA_UTENTE:-mt-dieci-2026}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10a6-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10a6}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10a6-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10a6}
export UNITA=${UNITA:-remotix-$PORTA}

# ⭐ I dieci, e l'undicesimo che sta a parte.
#
# ⛔ `QUANTI` e' il numero dei MIEI utenti, e l'uid segue il nome per
#    costruzione: `provamtN` → uid 1109+N.  ⚠ Un uid scelto a mano per ciascuno
#    sarebbe undici occasioni di scrivere il numero di qualcun altro.
QUANTI=${QUANTI:-10}
# ⭐ L'UNDICESIMO — `PIANO.md` fase 10 vuole sapere che cosa riceve chi arriva
#    quando i dieci ci sono gia'.  ⛔ Con `MAX_ATTACCATE` a 16 (`src/rcp.c:886`)
#    l'undicesimo ENTRA: la domanda non e' «viene rifiutato», e' «che cosa
#    riceve, e in che stato lascia gli altri dieci».
CON_UNDICESIMO=${CON_UNDICESIMO:-1}
[ "$CON_UNDICESIMO" = 1 ] && TOTALE=$((QUANTI + 1)) || TOTALE=$QUANTI

nome_utente() { printf 'provamt%d' "$1"; }
uid_utente()  { printf '%d' "$((1109 + $1))"; }

# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, e non si toccano mai.
VICINE=${VICINE:-"7700 7730 7900 7910 7920 8000 8010 8020 8030 8040 8050 8060 8070 8080 8090"}

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

	case "$PASSO" in
	stato)
		# ⛔ Gli ascoltatori che non sono miei si contano e basta.
		R=""
		for p in $VICINE; do
			R="$R$p:$(ss -uln 2>/dev/null | grep -c ":$p ") "
		done
		printf '    --  ascoltatori NON miei (si contano, non si toccano): %s\n' "$R"
		printf '    --  il mio server sulla %s: %s ascoltatore/i · unita\047 %s\n' \
			"$PORTA" "$(ss -uln 2>/dev/null | grep -c ":$PORTA ")" \
			"$(systemctl is-active "$UNITA.service" 2>/dev/null)"
		printf '    --  carico: %s\n' "$(uptime | sed 's/.*average/media/')"
		printf '    --  memoria: %s\n' "$(free -m | awk '/^Mem:/{printf "%d MiB usati su %d, %d disponibili", $3, $2, $7}')"
		guai=0
		i=1
		while [ "$i" -le "$TOTALE" ]; do
			u=$(nome_utente "$i"); n=$(uid_utente "$i")
			riga="    "
			if id "$u" >/dev/null 2>&1; then riga="$riga utente=si"; else riga="$riga utente=NO"; guai=$((guai+1)); fi
			# ⛔ `loginctl show-user` senza `2>/dev/null`: uno stato che non si
			#    legge NON e' «linger spento» (`CODER.md` §3.10).
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
			# ⛔⛔ IL PALCO ORFANO — quel che resta di un giro precedente.
			palco=$(pgrep -u "$n" -a 2>/dev/null | grep -cE 'gnome-shell|gnome-session|mutter|Xwayland|04-b30-scena|remotix' || true)
			tutti=$(pgrep -u "$n" -c 2>/dev/null || echo 0)
			if [ "$palco" != "0" ]; then
				riga="$riga ⛔PALCO-ORFANO=$palco (processi in tutto: $tutti)"
				guai=$((guai+1))
			else
				riga="$riga palco=pulito"
			fi
			printf '    --  %-10s uid %s %s\n' "$u" "$n" "$riga"
			i=$((i+1))
		done
		if [ "$guai" = 0 ]; then
			ok "i $TOTALE utenti ci sono, hanno linger e gruppi, e non c'e' nessun palco orfano"
			exit 0
		fi
		ko "⛔ $guai cose non tornano sul terreno: NON si misura cosi'"
		exit 2 ;;

	sgombra)
		# ⛔ SOLO i miei uid, e SOLO i processi del PALCO.
		#
		# ⚠ La prima stesura faceva `pkill -u <uid>` e basta: ammazzava anche il
		#   fondo che `enable-linger` tiene acceso — `systemd --user`, PipeWire,
		#   `dbus-daemon`, `[M]` **sette processi per utente**.  ⇒ Il giro dopo
		#   partiva su un terreno che quello prima aveva smontato, e i primi
		#   secondi di ogni sessione erano la RINASCITA di quel fondo invece
		#   dell'apertura del palco.  Un numero plausibile e sbagliato.
		#
		# ⛔ E mai per nome globale: sulla macchina ci sono i palchi di altri
		#   agenti, e un `pkill gnome-shell` li ammazzerebbe tutti.
		# ⛔ E la classe di caratteri `[.]` / `[/]` non e' un vezzo: senza,
		#   `pkill -f` combacia con la PROPRIA riga di comando e uccide la shell
		#   che lo sta eseguendo, lasciando la pulizia a meta' in silenzio.
		PALCO='gnome-shell|gnome-session|gnome-settings|mutter|Xwayland|dconf|04-b30-scena|remotix-figlio|ssh-agent|at-spi|gvfs|gjs|goa-|tracker|evolution|xdg-|gsd-|gcr-'
		log "Sgombro i MIEI palchi e i MIEI clienti (uid $(uid_utente 1)-$(uid_utente "$TOTALE"))"
		i=1
		while [ "$i" -le "$TOTALE" ]; do
			n=$(uid_utente "$i")
			pkill -u "$n" -f -- "$PALCO" 2>/dev/null
			i=$((i+1))
		done
		# ⚠ I clienti girano da root dentro il contenitore: si riconoscono dal
		#   file del giornale, che porta il MIO lavoro nel nome.
		pkill -f -- "--giornale [/]srv/remotix/tmp/10a6/" 2>/dev/null
		pkill -f "10-b92-cliente[.]py --cliente" 2>/dev/null
		sleep 3
		i=1; resti=0
		while [ "$i" -le "$TOTALE" ]; do
			n=$(uid_utente "$i")
			c=$(pgrep -u "$n" -a 2>/dev/null | grep -cE "$PALCO" || true)
			[ "$c" != "0" ] && { dub "uid $n ha ancora $c processi del palco: mando -9"; pkill -9 -u "$n" -f -- "$PALCO" 2>/dev/null; resti=$((resti+1)); }
			i=$((i+1))
		done
		sleep 1
		ok "sgomberato (con $resti insistenze) — ⭐ il fondo di «linger» resta in piedi apposta"
		exit 0 ;;

	orologio)
		# ⭐ L'ANCORA DELLA SALITA: l'orologio MONOTONO della macchina, in ms.
		#    ⛔ E' lo stesso orologio dei clienti (il contenitore e' un chroot
		#       sullo STESSO kernel) e lo stesso che il server mette nei 28 byte
		#       di §6.2.  Senza questo numero un gradino potrebbe leggere i
		#       fotogrammi del gradino precedente.
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
#    ruberebbe lo stdin a `sudo -S` (`09-b70-ritmo.py`, sopra `catena_root()`).
remoto() { ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $1 $SUL_SERVER $2"; }

PASSO=${1:-stato}
case "$PASSO" in
porta)
	log "1 · I sorgenti DELL'ALBERO DI LAVORO in $ALBERO"
	printf '    --  HEAD = %s (⚠ e NON e" quel che spedisco)\n' \
		"$(cd "$QUI" && git rev-parse --short HEAD)"
	for f in rcp.c figlio.c webtransport.c main.c; do
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
		banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py \
		banchi/10-b91-terreno-dieci.sh banchi/10-b92-dieci.py | \
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

	# ⛔⭐ E IL BINARIO CHE MISURO E' QUELLO CHE CREDO.  Si dichiara l'md5, e si
	#     LEGGONO dal binario i due tetti che questa fase esiste per mettere in
	#     discussione: `MAX_ATTACCATE` e `MAX_FIGLI`.  ⚠ Sono `#define`, quindi
	#     dal binario si legge la FRASE che li nomina, non il numero.
	log "3 · ⛔ CHE COSA HO COSTRUITO — e i due tetti, letti dai sorgenti SPEDITI"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
		 echo md5 binario:  \\\$(md5sum $ALBERO/src/remotix | cut -d' ' -f1)
		 echo md5 rcp.c:    \\\$(md5sum $ALBERO/src/rcp.c | cut -d' ' -f1)
		 echo md5 figlio.c: \\\$(md5sum $ALBERO/src/figlio.c | cut -d' ' -f1)
		 grep -n 'define MAX_ATTACCATE' $ALBERO/src/rcp.c
		 grep -n 'define MAX_FIGLI' $ALBERO/src/figlio.c
		 grep -n 'define MAX_IN_VOLO' $ALBERO/src/aiutante.c
		 grep -n 'define WT_PALCHI' $ALBERO/src/webtransport.c\"" \
		|| { ko "non ho potuto rileggere il binario"; exit 2; }
	exit 0 ;;

utenti)
	log "I $TOTALE utenti — ⛔ ciascuno delegato a 07-b64-terreno.sh, che e' certificato"
	inf "⛔ D12: la parola d'ordine NON passa da argv — file 0600 e chpasswd dallo stdin"
	inf "⛔ gruppi render,video e enable-linger per ciascuno, o il desktop non parte"
	i=1
	while [ "$i" -le "$TOTALE" ]; do
		u=$(nome_utente "$i"); n=$(uid_utente "$i")
		printf '\n  ── %d/%d · %s (uid %s) ──\n' "$i" "$TOTALE" "$u" "$n"
		# ⭐ Il MIO ambiente, e non una riga sua riscritta.
		if ! UTENTE="$u" UID_B="$n" bash "$QUI/banchi/07-b64-terreno.sh" utente; then
			ko "⛔ «$u» non si e' provvisto: mi fermo QUI invece di provvederne nove"
			exit 2
		fi
		i=$((i+1))
	done
	ok "$TOTALE utenti provvisti · la parola sta in $LAV/parola (0600), uguale per tutti"
	exec "$0" stato ;;

uno-per-volta)
	# ⛔⛔ LA VERIFICA CHE VIENE PRIMA DELLA SALITA.
	#     Se il quinto utente non arriva a `SESSIONE` da solo, un rosso al
	#     quinto gradino della salita **non e' del numero cinque**: e' suo.  E i
	#     due casi hanno la stessa faccia.
	log "⛔ CIASCUNO DEI $TOTALE ARRIVA A «SESSIONE» DA SOLO — prima di provarli insieme"
	inf "⚠ uno per volta: fra un utente e l'altro non c'e' NESSUNA sovrapposizione"
	exec python3 "$QUI/banchi/10-b92-dieci.py" uno-per-volta ;;

stato)   remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA QUANTI=$QUANTI CON_UNDICESIMO=$CON_UNDICESIMO VICINE='$VICINE'" stato ;;
sgombra) remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA QUANTI=$QUANTI CON_UNDICESIMO=$CON_UNDICESIMO" sgombra ;;
orologio) remoto "LAV=$LAV" orologio ;;
accendi|spegni|sblocca)
	# ⛔ Non se ne riscrive una riga: il MIO ambiente, e il file certificato.
	exec bash "$QUI/banchi/07-b64-terreno.sh" "$PASSO" ;;
*)
	ko "passo sconosciuto: $PASSO"
	sed -n '/^# Uso (dal portatile)/,/^# ===/p' "$0"
	exit 2 ;;
esac
