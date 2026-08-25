#!/usr/bin/env bash
# ===========================================================================
# 10-b0-innesta.sh — ⛔ I GUASTI DA INNESTARE PER CERTIFICARE `10-b0-terreno.sh`.
#
# Gira DA ROOT sulla macchina di prova, e lo spedisce `10-b0-certifica.sh`.
# ⛔ Non serve a nessun banco: serve a far vedere il ROSSO al controllo del
#    terreno.  Un controllo che non lo si e' visto mordere e' peggio che non
#    averlo — fa credere che qualcuno stia guardando.
#
# ⚠⚠ E OGNI GUASTO QUI DENTRO TOCCA COSE CONDIVISE con altri nove agenti che
#    stanno misurando adesso.  ⇒ Tutti hanno tre proprieta', e non sono
#    negoziabili:
#      1. durano SECONDI, non minuti (i processi finti muoiono da soli);
#      2. stanno su nomi MIEI dove si puo' (`…-CERTIFICA-…`);
#      3. hanno il loro «togli», e chi li innesta VERIFICA di averli tolti.
#
#   uso:  bash 10-b0-innesta.sh <passo> [argomenti]
# ===========================================================================
set -uo pipefail
LAV=${LAV:-/media/REMOTIX/tmp/10a7}
ALBERO=${ALBERO:-$LAV/albero-prova}
MARCA=10a7-CERTIFICA
FINTO=$LAV/$MARCA-remotix/src
TC=/usr/sbin/tc; [ -x "$TC" ] || TC=$(command -v tc)

case "${1:-}" in

# ── un processo «remotix» che NON e' mio ──────────────────────────────────
remotix-finto-avvia)
	mkdir -p "$FINTO"
	cp /bin/sleep "$FINTO/remotix"
	setsid "$FINTO/remotix" "${2:-25}" </dev/null >/dev/null 2>&1 &
	sleep 0.3
	pgrep -f "$MARCA-remotix/src/remotix" >/dev/null && echo INNESTATO || echo NON-INNESTATO
	;;
remotix-finto-togli)
	pkill -f "$MARCA-remotix/src/remotix" 2>/dev/null
	sleep 0.4
	pgrep -f "$MARCA-remotix/src/remotix" >/dev/null && echo RIMASTO || echo TOLTO
	;;

# ── qualcuno che tiene aperta la DISCRETA (il caso di fase 5) ─────────────
fd-discreta-avvia)
	N=$(readlink -f /dev/dri/by-path/pci-"${PCI_DISCRETA:-0000:03:00.0}"-render)
	[ -e "$N" ] || { echo NON-INNESTATO; exit 1; }
	# ⛔⭐ IL SEGNO VA IN `argv[0]`, NON IN UN COMMENTO.  `[M]` 24 agosto 2026:
	#    con `bash -c "exec 9<…; sleep N  # segno"` bash **si sostituisce**
	#    all'ultimo comando (l'ottimizzazione dell'ultimo `exec`), e da quel
	#    momento la riga di comando e' «sleep N»: il segno sparisce, `pgrep` non
	#    lo trova e `pkill` non lo ammazza.  ⇒ il guasto restava innestato per
	#    tutti i 40 s, e chi lo aveva messo credeva di non averlo messo.
	#    ⚠ `exec -a` mette il segno dentro `argv[0]`, che l'`exec` porta con se',
	#      e il descrittore 9 attraversa l'`exec` perche' non e' CLOEXEC.
	setsid bash -c "exec 9<$N; exec -a '$MARCA-FD' sleep ${2:-25}" </dev/null >/dev/null 2>&1 &
	sleep 0.4
	pgrep -f "$MARCA-FD" >/dev/null && echo "INNESTATO su $N" || echo NON-INNESTATO
	;;
fd-discreta-togli)
	pkill -f "$MARCA-FD" 2>/dev/null
	sleep 0.4
	pgrep -f "$MARCA-FD" >/dev/null && echo RIMASTO || echo TOLTO
	;;

# ── un cliente rimasto vivo sulla mia porta ───────────────────────────────
cliente-finto-avvia)
	setsid bash -c "exec -a 'python3 $LAV/01-b3-cliente.py --porta ${2:-7977} $MARCA' \
	                sleep ${3:-25}" </dev/null >/dev/null 2>&1 &
	sleep 0.4
	pgrep -f "b3-cliente.py --porta ${2:-7977}" >/dev/null && echo INNESTATO || echo NON-INNESTATO
	;;
cliente-finto-togli)
	pkill -f "b3-cliente.py --porta ${2:-7977}" 2>/dev/null
	sleep 0.4
	pgrep -f "b3-cliente.py --porta ${2:-7977}" >/dev/null && echo RIMASTO || echo TOLTO
	;;

# ── ⛔ IL `netem` SU `lo`, e chi lo mette ha gia' preso il suo lucchetto ──
netem-metti)
	"$TC" qdisc replace dev lo root netem delay "${2:-1}"ms || { echo NON-INNESTATO; exit 1; }
	"$TC" qdisc show dev lo | grep -q netem && echo INNESTATO || echo NON-INNESTATO
	;;
netem-togli)
	"$TC" qdisc del dev lo root 2>/dev/null
	# ⛔ E lo si VERIFICA: «l'ho tolto» detto a memoria e' la forma esatta del
	#    difetto che questo guasto certifica.
	if "$TC" qdisc show dev lo | grep -q netem; then echo RIMASTO; else
		echo "TOLTO · $("$TC" qdisc show dev lo | tr '\n' ' ')"; fi
	;;

# ── un lucchetto finto, intestato a un altro ──────────────────────────────
#    ⛔ SU UN POSTO MIO, mai su `/media/REMOTIX/tmp/.lucchetto-gpu.d`: quello
#       e' di chi sta misurando adesso, e non si tocca nemmeno per prova.
luc-finto)
	P=${LUCCHETTO:?serve LUCCHETTO}
	case "$P" in */.lucchetto-gpu.d) echo "⛔ RIFIUTO: quello e' il lucchetto VERO"; exit 1 ;; esac
	rm -rf "$P"; mkdir -p "$P"
	printf '%s %s\n' "$(( $(date +%s) + ${3:-600} ))" "${2:-10-zz-intruso}" >"$P/chi"
	cat "$P/chi"
	;;
luc-togli)
	P=${LUCCHETTO:?serve LUCCHETTO}
	case "$P" in */.lucchetto-gpu.d) echo "⛔ RIFIUTO"; exit 1 ;; esac
	rm -rf "$P"; [ -d "$P" ] && echo RIMASTO || echo TOLTO
	;;

# ── il binario piu' VECCHIO dei sorgenti — il caso che ha salvato la fase 1 ─
bin-vecchio)  touch "$ALBERO/src/main.c" && echo INNESTATO ;;
bin-nuovo)    touch "$ALBERO/src/remotix" && echo TOLTO ;;

# ── due binari nello stesso albero (il difetto D5) ────────────────────────
bin-doppio)   mkdir -p "$ALBERO/altrove" && cp -p "$ALBERO/src/remotix" "$ALBERO/altrove/remotix" && echo INNESTATO ;;
bin-singolo)  rm -rf "$ALBERO/altrove" && echo TOLTO ;;

# ── un binario che non lega ngtcp2 ────────────────────────────────────────
bin-falso)
	[ -f "$ALBERO/src/remotix.vero" ] || cp -p "$ALBERO/src/remotix" "$ALBERO/src/remotix.vero"
	cp /bin/true "$ALBERO/src/remotix"; touch "$ALBERO/src/remotix"; echo INNESTATO ;;
bin-vero)
	[ -f "$ALBERO/src/remotix.vero" ] && mv "$ALBERO/src/remotix.vero" "$ALBERO/src/remotix"
	touch "$ALBERO/src/remotix"; echo TOLTO ;;

# ── il ban dell'indirizzo, per dodici ore ─────────────────────────────────
ban-metti)
	printf '%s %s\n' "${2:-192.168.0.2}" "$(( $(date +%s) + 43200 ))" >"${BAN_FILE:-$LAV/ban-prova}"
	cat "${BAN_FILE:-$LAV/ban-prova}" ;;
ban-togli)
	rm -f "${BAN_FILE:-$LAV/ban-prova}"
	[ -f "${BAN_FILE:-$LAV/ban-prova}" ] && echo RIMASTO || echo TOLTO ;;

# ── che cosa e' rimasto addosso: si chiede, non si ricorda ────────────────
verifica)
	echo "netem su lo:   $("$TC" qdisc show dev lo | tr '\n' ' ')"
	echo "remotix finto: $(pgrep -cf "$MARCA-remotix/src/remotix")"
	echo "fd discreta:   $(pgrep -cf "$MARCA-FD")"
	echo "cliente finto: $(pgrep -cf "b3-cliente.py --porta")"
	echo "albero altrove:$( [ -d "$ALBERO/altrove" ] && echo C-E || echo no)"
	echo "remotix.vero:  $( [ -f "$ALBERO/src/remotix.vero" ] && echo C-E || echo no)"
	echo "ban di prova:  $( [ -f "${BAN_FILE:-$LAV/ban-prova}" ] && echo C-E || echo no)"
	echo "luc di prova:  $( [ -d "${LUCCHETTO:-/nessuno}" ] && echo C-E || echo no)"
	;;
*)
	echo "passi: remotix-finto-avvia|togli · fd-discreta-avvia|togli ·"
	echo "       cliente-finto-avvia|togli · netem-metti|togli · luc-finto|luc-togli ·"
	echo "       bin-vecchio|bin-nuovo|bin-doppio|bin-singolo|bin-falso|bin-vero ·"
	echo "       ban-metti|ban-togli · verifica"
	exit 2 ;;
esac
