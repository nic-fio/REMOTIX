#!/bin/bash
# 19-nvidia.sh — il banco della macchina NVIDIA a noleggio, guidato DAL PORTATILE.
#
#   bash banchi/19-nvidia/19-nvidia.sh prepara           # PRIMA del noleggio: la valigia
#   bash banchi/19-nvidia/19-nvidia.sh tutto IP          # manda, avvia, segue (riavvio compreso), raccoglie
#   bash banchi/19-nvidia/19-nvidia.sh pulisci IP        # DOPO aver raccolto: la macchina come trovata
#
#   e a pezzi:  manda IP · avvia IP [PASSO] · segui IP · stato IP · raccogli IP · entra IP
#
# Variabili: UTENTE (root; un utente con «sudo» senza parola va bene: ubuntu, debian, admin),
# PORTA_SSH (22), CHIAVE (un file di chiave ssh), CONTENITORE=nome (la prova LOCALE: podman exec
# al posto di ssh, per i passi che non toccano la scheda — vedi 19-nv-prova-contenitore.sh).
#
# La valigia (`prepara`) sta in costruzione-uscita/19-nvidia/ (ignorata da git): i .deb di
# REMOTIX per Debian 13 e Ubuntu 26.04 costruiti da QUESTO albero (si lancia da un checkout di
# `fase-19`), l'installatore, e i banchi che servono sulla macchina.  Le evidenze tornano in
# misure/19-nvidia/.
set -u
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
VAL=$USCITA/19-nvidia
MISURE=$ALBERO/misure/19-nvidia
LONTANO=/opt/remotix-nv
LAVORO=/var/lib/remotix-nv
UNITA=remotix-nv-banco
UTENTE=${UTENTE:-root}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s · %s\033[0m\n' "$(date +%H:%M:%S)" "$*"; }

# ── la strada verso la macchina: ssh, o podman exec per la prova locale ────────────────────
PRE=""
[ "$UTENTE" != root ] && PRE="sudo -n"
lontano() {  # lontano 'comando' — gira da root sulla macchina (il comando viaggia sullo stdin:
	#             niente virgolette da sfuggire, qualunque sia la shell di chi entra)
	if [ -n "${CONTENITORE:-}" ]; then
		printf '%s\n' "$1" | podman exec -i "$CONTENITORE" bash -s
	else
		printf '%s\n' "$1" | ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ConnectTimeout=15 \
			${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" "$PRE bash -s"
	fi
}

serve_ip() {
	IP=${1:-}
	[ -n "$IP" ] || [ -n "${CONTENITORE:-}" ] || { echo "serve l'indirizzo della macchina"; exit 2; }
	IP=${IP:-contenitore}
}

# ═══════════════════════════════════════════════════════════════════════════
prepara() {
	log "prepara: la valigia (prima del noleggio, sul portatile)"
	command -v podman >/dev/null || { ko "serve podman"; exit 2; }
	local ramo hash sporco=""
	ramo=$(git -C "$ALBERO" rev-parse --abbrev-ref HEAD)
	hash=$(git -C "$ALBERO" rev-parse --short HEAD)
	[ -n "$(git -C "$ALBERO" status --porcelain -- src packaging installatore banchi)" ] && sporco="+modifiche"
	[ "$ramo" = fase-19 ] || echo "    ⚠ il ramo e' «$ramo», non fase-19: la valigia porta $hash$sporco, e lo dice"
	rm -rf "$VAL/valigia"
	mkdir -p "$VAL/valigia/pacchetti" "$VAL/valigia/bin" "$VAL/valigia/albero"
	log "i .deb di REMOTIX (src/costruzione/costruisci-deb.sh debian13 ubuntu2604)"
	if ! USCITA=$USCITA bash "$ALBERO/src/costruzione/costruisci-deb.sh" debian13 ubuntu2604 > "$VAL/costruisci-deb.log" 2>&1; then
		ko "costruisci-deb.sh non riuscito ($VAL/costruisci-deb.log)"; tail -n 5 "$VAL/costruisci-deb.log"; exit 1
	fi
	cp "$USCITA"/deb-debian13/remotix_*.deb "$USCITA"/deb-ubuntu2604/remotix_*.deb "$VAL/valigia/pacchetti/" \
		|| { ko "i .deb non ci sono"; exit 1; }
	grep -h . "$USCITA"/deb-*/controlli.txt 2>/dev/null | sed 's/^/      /'
	ok "$(ls "$VAL/valigia/pacchetti" | tr '\n' ' ')"
	log "l'installatore (installatore/costruisci.sh)"
	bash "$ALBERO/installatore/costruisci.sh" > "$VAL/costruisci-installatore.log" 2>&1 \
		|| { ko "installatore non costruito ($VAL/costruisci-installatore.log)"; exit 1; }
	cp "$ALBERO/installatore/uscita/remotix-install" "$VAL/valigia/bin/"
	ok "remotix-install $("$VAL/valigia/bin/remotix-install" versione 2>/dev/null)"
	log "i banchi (come 15-porta.sh) e i sorgenti per il banco 19"
	albero_in_valigia
	{
		echo "$hash$sporco ($ramo) · $(git -C "$ALBERO" log -1 --format='%cd %s' --date=short HEAD | cut -c1-120)"
		echo "preparata: $(date -Is) su $(hostname)"
		(cd "$VAL/valigia" && sha256sum pacchetti/*.deb bin/remotix-install)
	} > "$VAL/valigia/VERSIONE"
	tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	ok "valigia: $VAL/valigia.tgz ($(du -h "$VAL/valigia.tgz" | cut -f1)) · $(head -1 "$VAL/valigia/VERSIONE")"
}

# i banchi e i sorgenti dell'albero di ADESSO dentro la valigia (non i pacchetti)
albero_in_valigia() {
	rm -rf "$VAL/valigia/albero"
	mkdir -p "$VAL/valigia/albero"
	(
		cd "$ALBERO" || exit 1
		{
			ls banchi/*.py banchi/*.sh banchi/*.html banchi/*.js 2>/dev/null
			find banchi/11-scatole banchi/15-suite banchi/19-vulkan banchi/19-nvidia -type f ! -name '*.pyc' \
				! -path '*/__pycache__/*' ! -name '*registro*.jsonl' ! -name 'rapporto-*'
			find src -maxdepth 1 -type f
		} | tar -cf - -T - | tar -xf - -C "$VAL/valigia/albero"
	)
}

manda() {
	log "manda la valigia a $IP"
	[ -f "$VAL/valigia.tgz" ] || { ko "manca la valigia: prima «$0 prepara»"; exit 1; }
	# ⛔ 5 ott 2026: PROVE e BROWSER_SUITE aggiunti al banco DOPO la valigia non arrivavano —
	#    `manda` spediva i banchi di quando la valigia era stata fatta, e la macchina girava la
	#    suite intera. ⇒ I banchi (non i pacchetti) si rinfrescano dall'albero a ogni `manda`,
	#    e la VERSIONE lo dice
	if [ -d "$VAL/valigia/pacchetti" ]; then
		albero_in_valigia
		sed -i '/^banchi rinfrescati:/d' "$VAL/valigia/VERSIONE"
		echo "banchi rinfrescati: $(date -Is) da $(git -C "$ALBERO" rev-parse --short HEAD)$( \
			[ -n "$(git -C "$ALBERO" status --porcelain -- banchi)" ] && echo +modifiche)" >> "$VAL/valigia/VERSIONE"
		tar -C "$VAL/valigia" -czf "$VAL/valigia.tgz" .
	fi
	if [ -n "${CONTENITORE:-}" ]; then
		podman exec "$CONTENITORE" mkdir -p "$LONTANO"
		podman exec -i "$CONTENITORE" tar -xzf - -C "$LONTANO" < "$VAL/valigia.tgz" || exit 1
	else
		ssh -o StrictHostKeyChecking=accept-new ${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" \
			"$PRE rm -rf $LONTANO && $PRE mkdir -p $LONTANO && $PRE tar -xzf - -C $LONTANO" < "$VAL/valigia.tgz" || exit 1
	fi
	ok "$(lontano "head -1 $LONTANO/VERSIONE")"
}

avvia() {
	local p=${1:-tutto}
	log "avvia «$p» sulla macchina (un'unita' di systemd: ssh puo' cadere)"
	if lontano "systemctl is-active --quiet $UNITA"; then ko "il banco gira gia' ($UNITA)"; return 1; fi
	lontano "mkdir -p $LAVORO && rm -f $LAVORO/uscita && echo '=== avvio $p $(date -Is)' >> $LAVORO/banco.log && \
		systemctl reset-failed $UNITA 2>/dev/null; \
		systemd-run --unit=$UNITA --collect --property=StandardOutput=append:$LAVORO/banco.log \
		--property=StandardError=append:$LAVORO/banco.log --setenv=FORZA=${FORZA:-0} --setenv=RIFAI='${RIFAI:-}' \
		--setenv=PROVE='${PROVE:-}' --setenv=BROWSER_SUITE='${BROWSER_SUITE:-}' --setenv=CLIENTE_SCHEDA='${CLIENTE_SCHEDA:-0}' \
		/bin/bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh $p" \
		&& ok "partito"
}

# segue il registro finche' il banco non scrive la sua uscita; torna quell'uscita
segui() {
	log "seguo il banco (Ctrl-C non lo ferma: rilancia «segui»)"
	local da=0 righe u
	da=$(lontano "wc -l < $LAVORO/banco.log" 2>/dev/null || echo 0)
	da=$(( ${da:-0} > 40 ? da - 40 : 0 ))
	while :; do
		righe=$(lontano "tail -n +$((da + 1)) $LAVORO/banco.log 2>/dev/null")
		if [ -n "$righe" ]; then
			printf '%s\n' "$righe"
			da=$((da + $(printf '%s\n' "$righe" | wc -l)))
		fi
		if ! lontano "systemctl is-active --quiet $UNITA" 2>/dev/null; then
			u=$(lontano "cat $LAVORO/uscita 2>/dev/null")
			[ -n "$u" ] && { log "il banco ha finito: uscita $u"; return "$u"; }
			# ssh caduto o macchina che riparte: si riprova
			lontano true 2>/dev/null || { sleep 20; continue; }
			log "il banco non gira e non ha scritto l'uscita (fermato a mano?)"; return 3
		fi
		sleep 20
	done
}

aspetta_ssh() {
	local i
	for i in $(seq 1 60); do
		sleep 15
		lontano true >/dev/null 2>&1 && { ok "la macchina risponde"; return 0; }
	done
	ko "dopo 15 minuti la macchina non risponde"; return 1
}

raccogli() {
	log "raccolgo l'archivio delle evidenze"
	lontano "bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh raccogli" | tail -n 3
	local nome sha
	nome=$(lontano "cat $LAVORO/archivio")
	sha=$(lontano "cat $LAVORO/archivio.sha256")
	[ -n "$nome" ] || { ko "nessun archivio"; return 1; }
	mkdir -p "$MISURE"
	lontano "cat $LAVORO/$nome" > "$MISURE/$nome"
	if [ "$(sha256sum "$MISURE/$nome" | cut -d' ' -f1)" = "$sha" ]; then
		lontano "touch $LAVORO/raccolto"
		ok "$MISURE/$nome (sha256 uguale)"
		tar -xzf "$MISURE/$nome" -O evidenze/passi.txt 2>/dev/null | sed 's/^/      /'
	else
		ko "sha256 diverso: rifai «raccogli»"; return 1
	fi
}

pulisci() {
	log "pulisco la macchina"
	lontano "FORZA=${FORZA:-0} bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh pulisci" || return 1
	lontano "rm -rf $LONTANO $LAVORO" && ok "valigia e cartella di lavoro tolte"
	lontano "cat /run/reboot-required 2>/dev/null; true"
}

tutto() {
	manda
	avvia tutto || exit 1
	segui; local u=$? n=0
	# piu' di un riavvio (5 ott 2026): l'aggiornamento di Ubuntu ne chiede uno per salto, il driver uno
	while [ "$u" = 10 ] && [ $n -lt 10 ]; do
		n=$((n + 1))
		log "il banco chiede un RIAVVIO ($n; aggiornamento/driver/ICD/modeset): riavvio e riprendo"
		[ -n "${CONTENITORE:-}" ] && { ko "in un contenitore non si riavvia"; exit 1; }
		lontano "systemctl reboot" || true
		aspetta_ssh || exit 1
		avvia tutto || exit 1
		segui; u=$?
	done
	raccogli
	log "FINE: uscita $u · le evidenze in $MISURE · la pulizia: «$0 pulisci $IP»"
	return "$u"
}

AZIONE=${1:-}
case "$AZIONE" in
prepara) prepara ;;
manda|segui|raccogli|pulisci|tutto) serve_ip "${2:-}"; "$AZIONE" ;;
avvia) serve_ip "${2:-}"; avvia "${3:-tutto}" ;;
stato) serve_ip "${2:-}"; lontano "bash $LONTANO/albero/banchi/19-nvidia/19-nv-macchina.sh stato" ;;
entra) serve_ip "${2:-}"; ssh ${CHIAVE:+-i "$CHIAVE"} -p "${PORTA_SSH:-22}" "$UTENTE@$IP" ;;
*) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
