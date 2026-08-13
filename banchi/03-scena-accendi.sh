#!/bin/bash
#
# 03-scena-accendi.sh — costruisce, accende e conta LA SCENA della fase 3.
#
#   bash 03-scena-accendi.sh costruisci
#   bash 03-scena-accendi.sh compositore-avvia      un Mutter headless TUTTO MIO
#   bash 03-scena-accendi.sh avvia [opzioni…]
#   bash 03-scena-accendi.sh conta
#   bash 03-scena-accendi.sh stato
#   bash 03-scena-accendi.sh ferma
#   bash 03-scena-accendi.sh compositore-ferma
#   bash 03-scena-accendi.sh istantanee N [opzioni…]   N fotogrammi consecutivi
#
# ===========================================================================
# ⛔ ISOLAMENTO — la regola del progetto, e qui morde per davvero
#
# Sulla macchina ci sono gia' dei server in ascolto, e **la 7561 e' quella che
# l'utente apre**: si legge, non si tocca.  A questo banco e' assegnata la
# **7602**, e tutto quel che e' suo porta quel numero addosso:
#
#     WAYLAND_DISPLAY   remotix-scena-7602      (⛔ NON wayland-0)
#     /dev/shm/         remotix-scena-7602
#     cartella          /tmp/remotix-03-scena-7602
#
# ⛔⛔ E LA COSA PIU' IMPORTANTE DI QUESTO FILE: **la scena NON si accende sulla
#      sessione dell'utente.**  Il 13 agosto 2026 questa macchina aveva
#      `gnome-shell` su **seat0, tty2, Active=yes**, cioe' l'utente davanti allo
#      schermo con Chrome aperto.  Un client a schermo intero e opaco su
#      `wayland-0` gli avrebbe coperto il desktop.
#
#   ⇒ `compositore-avvia` fa partire un **Mutter headless tutto nostro**, con un
#     monitor virtuale e un `--wayland-display` proprio.  Non e' un ripiego: e'
#     la stessa forma che la fase 3 usera' per misurare, ed e' l'unico modo di
#     far girare un client a schermo intero senza togliere lo schermo a
#     qualcuno.  ⚠ `avvia` senza `compositore-avvia` usa quel che c'e' in
#     `WAYLAND_DISPLAY`, e allora lo schermo se lo prende davvero.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PORTA=${PORTA:-7602}
LAV=${LAV:-/tmp/remotix-03-scena-$PORTA}
DISPLAY_W=${DISPLAY_W:-remotix-scena-$PORTA}
SHM=${SHM:-remotix-scena-$PORTA}
MONITOR=${MONITOR:-1280x720}
BIN=$LAV/03-scena
PIDF_SCENA=$LAV/scena.pid
PIDF_COMP=$LAV/compositore.pid
LOG_COMP=$LAV/compositore.log
LOG_SCENA=$LAV/scena.log

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

mkdir -p "$LAV"

# ⛔ Le porte che NON sono mie si contano prima e dopo: se calano, il giro ha
#    fatto un danno, e un danno che nessuno conta non e' successo.
vicini()
{
	local a b c
	a=$(ss -tuln 2>/dev/null | grep -c ':7448\b')
	b=$(ss -tuln 2>/dev/null | grep -c ':7501\b')
	c=$(ss -tuln 2>/dev/null | grep -c ':7561\b')
	printf '7448: %s · 7501: %s · 7561: %s ascoltatori' "$a" "$b" "$c"
}

# ---------------------------------------------------------------------------
costruisci()
{
	log "Costruisco la scena"
	local proto=/usr/share/wayland-protocols
	local scanner; scanner=$(command -v wayland-scanner) || {
		ko "wayland-scanner non c'e': non posso generare i protocolli"; return 1; }
	inf "wayland-scanner: $scanner"

	local xdg=$proto/stable/xdg-shell/xdg-shell.xml
	local pres=$proto/stable/presentation-time/presentation-time.xml
	for f in "$xdg" "$pres"; do
		[ -s "$f" ] || { ko "manca «$f»"; return 1; }
	done

	"$scanner" client-header "$xdg"  "$LAV/xdg-shell-client-protocol.h" || return 1
	"$scanner" private-code  "$xdg"  "$LAV/xdg-shell-protocol.c" || return 1
	"$scanner" client-header "$pres" "$LAV/presentation-time-client-protocol.h" || return 1
	"$scanner" private-code  "$pres" "$LAV/presentation-time-protocol.c" || return 1
	ok "quattro file generati da wayland-scanner"

	# ⛔⭐ SI COMPILA SU UN NOME NUOVO E POI SI RINOMINA — 13 agosto 2026.
	#
	#    Il coordinatore riporta che una build a `/media/REMOTIX/src/03-scena`
	#    era **in uso da un altro banco e non si sovrascriveva**: il nucleo
	#    rifiuta di scrivere su un eseguibile in esecuzione (`ETXTBSY`), e
	#    `gcc -o` falliva a meta' lasciando **un binario troncato** — cioe' un
	#    banco che parte e non si sa che cosa esegue.
	#
	#    ⭐ `rename(2)` e' atomico e non tocca l'inode vecchio: chi sta girando
	#      continua col suo, e il prossimo avvio prende il nuovo.  ⚠ E il file
	#      nuovo si crea NELLA STESSA cartella, o il rename attraversa un
	#      filesystem e non e' piu' atomico.
	local nuovo="$BIN.nuovo.$$"
	gcc -O2 -Wall -Wextra -o "$nuovo" \
	    "$QUI/03-scena.c" "$LAV/xdg-shell-protocol.c" "$LAV/presentation-time-protocol.c" \
	    -I"$LAV" $(pkg-config --cflags --libs wayland-client) -lrt || {
		rm -f "$nuovo"; ko "la compilazione e' fallita"; return 1; }
	mv -f "$nuovo" "$BIN" || {
		rm -f "$nuovo"
		ko "⛔ non riesco a mettere il binario al suo posto («$BIN»)."
		ko "   ⚠ Se un altro banco lo sta usando, usa una cartella tua:"
		ko "   LAV=/tmp/mia-cartella bash $0 costruisci"
		return 1; }
	ok "$BIN  ($(stat -c %s "$BIN") byte, sha $(sha256sum "$BIN" | cut -c1-16))"
	return 0
}

# ---------------------------------------------------------------------------
compositore_vivo()
{
	[ -f "$PIDF_COMP" ] && [ -d "/proc/$(cat "$PIDF_COMP" 2>/dev/null)" ]
}

compositore_avvia()
{
	log "Il compositore: un Mutter headless TUTTO MIO, monitor virtuale $MONITOR"
	inf "$(vicini)"
	if compositore_vivo; then
		ok "c'e' gia': pid $(cat "$PIDF_COMP") su WAYLAND_DISPLAY=$DISPLAY_W"
		return 0
	fi
	# ⛔ `--headless` invece di `--nested`: nested aprirebbe una finestra sullo
	#    schermo dell'utente.  E `--virtual-monitor` NON e' facoltativo — una
	#    sessione headless senza monitor virtuale parte viva, completa e NERA
	#    (`gnome.md` §13, prova M9), e la scena non avrebbe dove andare.
	rm -f "$LOG_COMP"
	setsid --fork env \
	    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
	    sh -c "exec >>'$LOG_COMP' 2>&1; exec mutter --headless --no-x11 \
	           --wayland --wayland-display '$DISPLAY_W' \
	           --virtual-monitor '$MONITOR'"
	# ⛔ Non si aspetta un silenzio: si aspetta un EVENTO — il socket —, con un
	#    tetto dichiarato.  `sleep 2 && spero` e' il modo in cui un banco
	#    diventa intermittente.
	local sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$DISPLAY_W"
	local g=0
	while [ $g -lt 60 ]; do
		[ -S "$sock" ] && break
		sleep 0.25; g=$((g+1))
	done
	if [ ! -S "$sock" ]; then
		ko "il socket «$sock» non e' comparso in 15 s.  Il registro dice:"
		tail -n 20 "$LOG_COMP" 2>/dev/null | sed 's/^/        /'
		return 1
	fi
	pgrep -u "$(id -u)" -f -- "--wayland-display $DISPLAY_W" | head -1 > "$PIDF_COMP"
	ok "compositore pid $(cat "$PIDF_COMP") · socket $sock"
	inf "$(vicini)"
	return 0
}

compositore_ferma()
{
	log "Fermo il compositore"
	if ! compositore_vivo; then ok "non c'era"; rm -f "$PIDF_COMP"; return 0; fi
	local pid; pid=$(cat "$PIDF_COMP")
	kill "$pid" 2>/dev/null
	local g=0
	while [ -d "/proc/$pid" ] && [ $g -lt 40 ]; do sleep 0.25; g=$((g+1)); done
	if [ -d "/proc/$pid" ]; then ko "il pid $pid non e' morto"; return 1; fi
	rm -f "$PIDF_COMP"
	ok "fermato (pid $pid)"
	inf "$(vicini)"
	return 0
}

# ---------------------------------------------------------------------------
scena_viva()
{
	[ -f "$PIDF_SCENA" ] && [ -d "/proc/$(cat "$PIDF_SCENA" 2>/dev/null)" ]
}

avvia()
{
	[ -x "$BIN" ] || { ko "la scena non e' costruita: «$0 costruisci»"; return 1; }
	if scena_viva; then ko "c'e' gia' una scena: pid $(cat "$PIDF_SCENA")"; return 1; fi
	local disp=$DISPLAY_W
	if ! [ -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$disp" ]; then
		# ⛔ Si DICHIARA il ripiego invece di prenderlo in silenzio: senza
		#    questa riga, «la scena gira sul compositore mio» e «la scena ha
		#    coperto il desktop dell'utente» avrebbero lo stesso aspetto.
		ko "⛔ il compositore mio non c'e' («$disp»).  NON ripiego su"
		ko "   WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-(niente)}: un client a schermo"
		ko "   intero e opaco li' coprirebbe il desktop dell'utente."
		ko "   ⇒ «$0 compositore-avvia», oppure DISPLAY_W=… se sai che fai."
		return 1
	fi
	rm -f "$LOG_SCENA"
	setsid --fork env \
	    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
	    WAYLAND_DISPLAY="$disp" \
	    sh -c "exec >>'$LOG_SCENA' 2>&1; exec '$BIN' --shm '$SHM' --loquace $*"
	local g=0
	while [ $g -lt 40 ]; do
		pgrep -u "$(id -u)" -f -- "$BIN --shm $SHM" >/dev/null 2>&1 && break
		sleep 0.1; g=$((g+1))
	done
	pgrep -u "$(id -u)" -f -- "$BIN --shm $SHM" | head -1 > "$PIDF_SCENA"
	if ! scena_viva; then
		ko "la scena non e' partita.  Il registro dice:"
		tail -n 20 "$LOG_SCENA" 2>/dev/null | sed 's/^/        /'
		return 1
	fi
	ok "scena pid $(cat "$PIDF_SCENA") su WAYLAND_DISPLAY=$disp"
	return 0
}

ferma()
{
	if ! scena_viva; then ok "non c'era nessuna scena"; rm -f "$PIDF_SCENA"; return 0; fi
	local pid; pid=$(cat "$PIDF_SCENA")
	kill "$pid" 2>/dev/null
	local g=0
	while [ -d "/proc/$pid" ] && [ $g -lt 40 ]; do sleep 0.25; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { ko "il pid $pid non e' morto"; return 1; }
	rm -f "$PIDF_SCENA"
	ok "scena fermata (pid $pid)"
	tail -n 3 "$LOG_SCENA" 2>/dev/null | sed 's/^/        /'
	return 0
}

# ---------------------------------------------------------------------------
case "${1:-stato}" in
costruisci)        costruisci ;;
compositore-avvia) compositore_avvia ;;
compositore-ferma) compositore_ferma ;;
avvia)             shift; avvia "$@" ;;
ferma)             log "Fermo la scena"; ferma ;;
conta)
	# ⛔ Il conteggio dei disegni del client, letto DA FUORI.  E' il controllo
	#    di `LEZIONI.md` §1.1 che dice se il tetto e' del compositore o della
	#    scena: se il client disegna 60 e il compositore ne presenta 37, il
	#    tetto NON e' nostro; se il client ne disegna 37, Mutter non c'entra.
	python3 "$QUI/03-marca.py" conta --shm "$SHM" ;;
stato)
	log "Lo stato"
	inf "$(vicini)"
	inf "cartella   $LAV"
	inf "binario    $([ -x "$BIN" ] && echo "$BIN sha $(sha256sum "$BIN" | cut -c1-16)" || echo 'NON costruito')"
	if compositore_vivo; then ok "compositore pid $(cat "$PIDF_COMP") · $DISPLAY_W"
	else inf "compositore: nessuno"; fi
	if scena_viva; then ok "scena pid $(cat "$PIDF_SCENA")"
	else inf "scena: nessuna"; fi
	python3 "$QUI/03-marca.py" conta --shm "$SHM" ;;
matrice)
	# ⛔⭐ IL CONTROLLO DI `LEZIONI.md` §1.1: DI CHI E' IL TETTO?
	#
	#    Si gira la stessa scena con i tre movimenti e i due danni, e si
	#    stampano accanto TRE numeri che non sono lo stesso numero:
	#      `disegni`     quante volte il client ha dipinto
	#      `presentati`  quante volte il compositore dice di aver messo sullo
	#                    schermo — ⭐ chiesto a lui, non dedotto
	#      `attese`      quante volte il client ha dovuto ASPETTARE un buffer
	#
	#    ⇒ `disegni` alto e `presentati` basso  ⇒ il tetto e' del compositore;
	#      `attese` > 0                        ⇒ il tetto e' NOSTRO;
	#      i due numeri uguali e bassi         ⇒ e' il monitor virtuale.
	#    ⛔ Senza questi tre, un numero solo attribuirebbe a Mutter un tetto
	#      che puo' essere della scena — che e' esattamente il 7 agosto.
	shift
	SEC=${1:-5}
	# ⛔ La misura si legge da quel che il COMPOSITORE ha dato alla scena, non
	#    dalla variabile `$MONITOR` di questa shell: la variabile dice quel che
	#    ho chiesto quando ho acceso il compositore, e se il compositore fosse
	#    gia' acceso con un'altra misura l'intestazione direbbe una cosa e i
	#    numeri ne misurerebbero un'altra (`LEZIONI.md` §1.11 punto 2: si
	#    verifica che abbia obbedito).
	log "La matrice dei tetti — $SEC s per cella"
	printf '        %-10s %-8s %8s %8s %8s %8s %10s\n' \
	    movimento danno disegni present. scartati attese misura
	for m in marca barra pieno; do
		for d in preciso pieno; do
			r=$(env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
			    WAYLAND_DISPLAY="$DISPLAY_W" \
			    "$BIN" --shm "$SHM" --giro "matrice-$m-$d" \
			    --movimento "$m" --danno "$d" --secondi "$SEC" 2>/dev/null)
			echo "$r" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('        %-10s %-8s %8.1f %8.1f %8d %8d %10s' % ('$m','$d',
      d['disegni']/d['secondi'], d['presentati']/d['secondi'],
      d['scarti_presentazione'], d['attese'],
      '%dx%d' % (d['larghezza'], d['altezza'])))"
		done
	done
	inf "⚠ i «presentati» valgono solo se presentazione_disponibile e' true"
	;;
istantanee)
	shift
	n=${1:-2}; shift || true
	log "Scarico $n fotogrammi consecutivi"
	rm -f "$LAV"/fotogramma-*.rgb24 "$LAV"/fotogramma-*.json
	avvia --istantanee "$n" --istantanea-prefisso "$LAV/fotogramma" "$@" || exit 1
	g=0
	while scena_viva && [ $g -lt 120 ]; do sleep 0.25; g=$((g+1)); done
	ferma >/dev/null 2>&1
	rm -f "$PIDF_SCENA"
	ls -l "$LAV"/fotogramma-*.rgb24 2>/dev/null | sed 's/^/        /'
	tail -n 2 "$LOG_SCENA" 2>/dev/null | sed 's/^/        /' ;;
*)
	echo "uso: $0 {costruisci|compositore-avvia|compositore-ferma|avvia|conta|stato|ferma|istantanee N}" >&2
	exit 2 ;;
esac
