#!/bin/bash
#
# 02-giudizio-mira-scena.sh — ⭐⭐ METTE LA MIRA DI F2.6 SUL MONITOR VIRTUALE
# che il PRODOTTO cattura, e la toglie.  Gira su CHUWI, tocca NIC-OS via ssh.
#
#   bash banchi/02-giudizio-mira-scena.sh stato
#   bash banchi/02-giudizio-mira-scena.sh metti cat1        (poi: riaccendi)
#   bash banchi/02-giudizio-mira-scena.sh via               (poi: riaccendi)
#   bash banchi/02-giudizio-mira-scena.sh riaccendi         ⛔ la 7561, da root
#
# ⛔ Porta di questo giro: **7611**.  7448, 7501 e 7561 si CONTANO prima e dopo.
#
# ===========================================================================
# ⛔⭐ PERCHE' LA MIRA E' LO **SFONDO**, E NON UNA FINESTRA A SCHERMO INTERO
#
# La prima idea — `mpv --fs --fs-screen-name=Meta-1`, come fa F2.2 — **non puo'
# funzionare qui**, e la ragione e' un invariante del prodotto, non un dettaglio:
#
#   · il monitor che il prodotto cattura **e' il suo**: `mutter.c` chiama
#     `RecordVirtual`, e Mutter gli monta un monitor nuovo — `[M]` 13 agosto
#     2026, `Meta-1` / **«Virtual remote monitor»**, a (1920,0), accanto al
#     `Meta-0` / «MetaVirtualMonitor» della sessione;
#   · quel monitor **nasce col figlio e muore con lui** (I4: il palco appartiene
#     alla sessione, il figlio cattura UNA volta e sopravvive al distacco);
#   · e il fotogramma viene preso **subito**: `[M]` fra «monitor virtuale
#     montato» e «fotogramma catturato» passano **95 ms**.
#
# ⇒ Non c'e' nessun istante in cui una finestra possa essere portata sul monitor
#   che verra' catturato: quando esiste, e' gia' stato catturato.  ⛔ E provarci
#   comunque avrebbe dato la peggiore delle uscite — la finestra sul monitor
#   SBAGLIATO, cioe' un metro puntato sul buio mentre dichiara la mira (e' il
#   difetto che F2.2 ha pagato il 12 agosto: `Meta-0` invece di `Meta-1`).
#
# ⭐ Lo **sfondo del desktop**, invece, GNOME lo dipinge su OGNI monitor dal
#   primo fotogramma, compreso uno appena nato.  ⇒ e' l'unica cosa che sul
#   monitor del prodotto c'e' **gia'** quando la cattura scatta — ed e' anche
#   la ragione per cui il desktop dell'utente si vedeva: quel monitor non ha
#   ne' barra in alto (sta sul primario) ne' icone.
#
# ⚠ `picture-options` = **`stretched`**: a 1920x1080 su un monitor 1920x1080
#   non scala niente ed e' 1:1.  ⛔ `spanned` spalmerebbe l'immagine sui DUE
#   monitor, cioe' meta' mira per monitor, e il metro cercherebbe le zone dove
#   non sono.  `[M]` verificato sui pixel della cattura: il pettine a passo 1 px
#   esce **250 / 5 / 250 / 5**, cioe' nessun filtro l'ha toccato.
#
# ===========================================================================
# ⛔ E DOPO AVER MESSO (O TOLTO) LA MIRA, IL SERVER SI RIACCENDE
#
# Il figlio cattura UNA volta, all'ingresso, e sopravvive al distacco: cambiare
# lo sfondo **non** cambia il fotogramma di un figlio gia' vivo.  ⇒ o si
# riaccende la 7561 (e il prossimo ingresso ricattura), oppure si misura la
# scena di prima credendo di misurare quella di adesso — che e' il guasto
# «fotogramma del giro precedente» innestato da noi, senza volerlo.
#
# ⛔ La 7561 gira **da root** (`setgroups` vuole root, `DECISIONI.md` §1.10-bis),
#    e si riaccende con `02-figlio-accendi.sh`, mai a mano.
# ⛔ E MAI una redirezione attorno a `ssh` o a `sshpw.py` — pagata sei volte.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)
SSHPW=$RADICE/v1/strumenti/sshpw.py
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7561}
# ⚠ I due valori di PRIMA, letti dalla macchina il 13 agosto 2026 e scritti qui
#   perche' «rimettere com'era» non sia una ricostruzione a memoria.
VIA_URI=${VIA_URI:-file:///usr/share/images/desktop-base/desktop-background.xml}
VIA_URI_SCURO=${VIA_URI_SCURO:-file:///usr/share/backgrounds/gnome/adwaita-d.jpg}
VIA_OPZIONI=${VIA_OPZIONI:-zoom}
REMOTA=${REMOTA:-/media/REMOTIX/tmp/02-giudizio-mira}
SRC=${SRC:-/media/REMOTIX/src}
D=${D:-/media/REMOTIX/src/remotix}
LAV=${LAV:-/media/REMOTIX/tmp/02-montaggio}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ⛔ L'ambiente della sessione si dichiara: senza `XDG_RUNTIME_DIR` e senza il
#    bus, `gsettings` scrive in un dconf che non e' quello della sessione viva —
#    e il comando riesce, cioe' il silenzio ha la faccia del successo (E8).
AMB="export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus;"
la() { timeout 300 ssh -o BatchMode=yes -o ConnectTimeout=10 "nicfio@$IND" "$AMB $1"; }

vicini() {
	local r=""
	for p in 7448 7501 7561; do
		r="$r$p: $(ssh -o BatchMode=yes -o ConnectTimeout=8 "nicfio@$IND" \
		           "ss -tuln | grep -c ':$p\b'" 2>/dev/null | tr -d '\r') · "
	done
	printf '%s\n' "${r%· }"
}

stato() {
	log "Lo sfondo della sessione, adesso"
	la "gsettings get org.gnome.desktop.background picture-uri;
	    gsettings get org.gnome.desktop.background picture-uri-dark;
	    gsettings get org.gnome.desktop.background picture-options" \
		| sed 's/^/    --  /'
	log "I monitor — ⛔ per NOME DEL PRODOTTO, mai per indice"
	la "bash $SRC/02-sessione-guardia.sh 2>&1 | tail -6" | sed 's/^/    /'
	inf "$(vicini)"
}

case "${1:-stato}" in
stato) stato; exit 0 ;;

metti)
	GIRO=${2:-}
	[ -n "$GIRO" ] || { ko "⛔ uso: $0 metti <giro>  (es. cat1)"; exit 2; }
	log "0. Il terreno"
	inf "$(vicini)"
	# ⛔ La mira si COSTRUISCE qui e si SPEDISCE: prendere quella che c'e' gia'
	#    di la' vorrebbe dire giudicare contro un'immagine che nessuno ha
	#    rifatto, e due giri con lo stesso nome sono la STESSA scena (il seme
	#    del rumore e' il nome del giro) — cioe' M6 spento senza dirlo.
	T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
	python3 "$QUI/02-giudizio-mira.py" --giro "$GIRO" --cartella "$T" \
		--larghezza 1920 --altezza 1080 >/dev/null || {
		ko "⛔ la mira non si e' costruita"; exit 2; }
	[ -s "$T/mira-$GIRO.png" ] || { ko "⛔ manca la copia a 8 bit da mettere a"
		ko "   sfondo (serve python3-pil sulla macchina di qua)"; exit 2; }
	ok "mira «$GIRO» costruita: 1920x1080"
	la "mkdir -p $REMOTA" >/dev/null || { ko "⛔ non ho preparato $REMOTA"; exit 2; }
	timeout 300 scp -o BatchMode=yes -q "$T/mira-$GIRO.png" \
		"nicfio@$IND:$REMOTA/mira-$GIRO.png" || {
		ko "⛔ la mira non e' arrivata sul server"; exit 2; }
	# ⛔ E si verifica che sia ARRIVATA QUELLA: un file troncato e un file
	#    giusto hanno la stessa faccia in `ls`.
	qua=$(md5sum "$T/mira-$GIRO.png" | cut -d' ' -f1)
	la_=$(la "md5sum $REMOTA/mira-$GIRO.png" | awk '{print $1}' | tr -d '\r')
	[ "$qua" = "$la_" ] || { ko "⛔ l'impronta non torna: qua $qua, la' $la_"; exit 2; }
	ok "⭐ spedita e verificata sull'impronta: $qua"

	log "1. La metto a sfondo — su TUTTI i monitor, compreso quello che nascera'"
	la "gsettings set org.gnome.desktop.background picture-options 'stretched';
	    gsettings set org.gnome.desktop.background picture-uri 'file://$REMOTA/mira-$GIRO.png';
	    gsettings set org.gnome.desktop.background picture-uri-dark 'file://$REMOTA/mira-$GIRO.png';
	    sleep 2;
	    gsettings get org.gnome.desktop.background picture-uri" | sed 's/^/    --  /'
	printf '\n'
	inf "⛔ ADESSO SERVE «$0 riaccendi»: un figlio gia' vivo tiene il"
	inf "   fotogramma di prima, e misurarlo sarebbe il guasto «precedente»"
	inf "   innestato da noi."
	exit 0 ;;

via)
	log "Rimetto lo sfondo di prima — ⭐ perche' l'utente giudica IL SUO desktop"
	# ⛔ Il giudizio della fase 2 (I8) e' «il proprio desktop dentro una
	#    scheda»: lasciare la mira significherebbe consegnargli una mira e
	#    chiamarla desktop.  La mira e' lo strumento, non la consegna.
	la "gsettings set org.gnome.desktop.background picture-options '$VIA_OPZIONI';
	    gsettings set org.gnome.desktop.background picture-uri '$VIA_URI';
	    gsettings set org.gnome.desktop.background picture-uri-dark '$VIA_URI_SCURO';
	    sleep 2;
	    gsettings get org.gnome.desktop.background picture-uri;
	    gsettings get org.gnome.desktop.background picture-options" | sed 's/^/    --  /'
	printf '\n'
	inf "⛔ e anche qui serve «$0 riaccendi»."
	exit 0 ;;

riaccendi)
	log "Riaccendo la $PORTA — DA ROOT, con lo script di P2.7"
	inf "$(vicini)"
	timeout 600 python3 "$SSHPW" \
		"sudo -S -p 'Password sudo: ' env PORTA=$PORTA D=$D LAV=$LAV \
		 bash $SRC/02-figlio-accendi.sh riaccendi" || {
		ko "⛔ la $PORTA NON e' tornata su: e' la porta che l'utente apre"; exit 3; }
	# ⛔ E il controllo che conta non e' «e' accesa»: e' «serve LA PAGINA
	#    CURATA».  Il processo legge il file una volta sola all'accensione.
	n=$(curl -k -s --max-time 15 "https://$IND:$PORTA/" | grep -c 'adatta_vista')
	if [ "${n:-0}" -gt 0 ]; then
		ok "⭐ la pagina servita porta «adatta_vista» $n volte: e' quella curata"
	else
		ko "⛔ la pagina servita NON e' quella curata: l'immagine tornerebbe"
		ko "   piccola, ed e' il difetto che l'utente ha trovato stamattina"
		exit 3
	fi
	inf "$(vicini)"
	exit 0 ;;

*) echo "uso: $0 [stato|metti <giro>|via|riaccendi]"; exit 2 ;;
esac
