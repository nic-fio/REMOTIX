#!/bin/bash
#
# 04-b26-lancia.sh — ⛔ GIRA SUL SERVER (NIC-OS), fuori dal contenitore, da root.
# Accende il banco dell'anello A6 della fase 4: il cursore.
#
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh terreno
#
# ⛔ E la costruzione gira DENTRO il contenitore, dove i percorsi hanno altri
#    nomi (`/media/REMOTIX/src` → `/srv/src`, `/media/REMOTIX` → `/srv/remotix`):
#
#   printf '%s\n' <pw> | bash /media/REMOTIX/enter.sh --root \
#     'SRC=/srv/src D=/srv/src/04-b26-src LAV=/srv/remotix/tmp/04-b26 \
#      bash /srv/src/04-b26-lancia.sh costruisci'
#
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh senza        ⛔ IL DIFETTO
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh con          ⭐ il controllo positivo
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh incorporato  ⭐ cursor-mode = 1
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh prodotto     la catena vera
#   sudo bash /media/REMOTIX/src/04-b26-lancia.sh tutto
#
# ===========================================================================
# ⛔ IL PERIMETRO, E PERCHE' NON HA PORTE
#
# All'anello A6 sono assegnate le porte **7651-7655** e non ne usa NESSUNA: il
# banco non apre un filo: parla al bus di sessione dell'utente `prova` e legge
# PipeWire.  ⇒ Si dichiara invece di tacere, perche' «non ne ha bisogno» e «se
# ne e' dimenticato» hanno lo stesso aspetto.
#
# ⛔ LE QUATTRO PORTE CHE NON SI TOCCANO — **7448**, **7501**, **7561**, **7571** —
#    si CONTANO prima e dopo lo stesso: se questo banco le smuovesse, la cosa da
#    sapere e' che le ha smosse, non che «non dovrebbe».
#
# ===========================================================================
# ⭐⭐ L'UTENTE `prova`, E NON SI RICREA (deciso dall'utente il 14 agosto 2026)
#
# `prova` (uid 1001) ha una sessione GNOME viva **senza `--virtual-monitor`**:
# `GetCurrentState` → 0 monitor, e il monitor che si cattura e' l'unico, quindi
# ⭐ **la shell ci va sopra**.  E' l'unico posto dove oggi esiste un desktop
# vero, quindi ⛔ **l'unico dove esiste un cursore vero da guardare**.
# `SPECIFICHE.md` §5.1 da' una sola sessione grafica per utente: ricrearla
# significherebbe perderla.
#
# ⛔ NON si usa `nicfio`: la sua sessione ha gia' un monitor suo.
#
# ===========================================================================
# ⛔ SI COSTRUISCE NEL CONTENITORE, SI ESEGUE SULL'HOST
#
# `[M]` 14 agosto 2026: sull'host non c'e' ne' `cc` ne' `pkg-config` — la
# sessione di `prova` pero' gira **li'**, non nel contenitore.  ⇒ Il binario si
# compila di la' e si esegue di qua, e le librerie sono le stesse (stesso
# Debian).  ⚠ Se un giorno divergessero, il sintomo sarebbe un
# `libpipewire … not found` all'avvio: e' dichiarato qui perche' non si perda
# mezz'ora a cercarlo altrove.
set -uo pipefail

SRC=${SRC:-/media/REMOTIX/src}
D=${D:-$SRC/04-b26-src}
LAV=${LAV:-/media/REMOTIX/tmp/04-b26}
UTENTE=${UTENTE:-prova}
UID_UTENTE=${UID_UTENTE:-1001}
XDG=/run/user/$UID_UTENTE

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

porte_intoccabili()
{
	log "le quattro porte che non si toccano — $1"
	if ! command -v ss >/dev/null 2>&1; then
		ko "\`ss\` non c'e': ⛔ NON GUARDATE (che non e «libere»)"
		return
	fi
	for p in 7448 7501 7561 7571; do
		if ss -ltn "sport = :$p" 2>/dev/null | grep -q LISTEN; then
			inf "$p in ascolto"
		else
			inf "$p non in ascolto"
		fi
	done
	inf "le mie (7651-7655): il banco non ne apre nessuna, e lo DICE"
}

terreno()
{
	log "il terreno"

	if id "$UTENTE" >/dev/null 2>&1; then
		ok "l'utente $UTENTE c'e' (uid $(id -u "$UTENTE"))"
	else
		ko "l'utente $UTENTE NON c'e': ⛔ non si ricrea da qui — vedi F5-desktop-vero.md"
		return 1
	fi

	if [ -S "$XDG/bus" ]; then
		ok "il bus di sessione di $UTENTE c'e' ($XDG/bus)"
	else
		ko "nessun bus di sessione in $XDG: la sessione non e' viva"
		return 1
	fi

	if pgrep -u "$UTENTE" -f 'gnome-shell' >/dev/null 2>&1; then
		ok "gnome-shell gira per $UTENTE"
		if pgrep -u "$UTENTE" -f 'gnome-shell.*--virtual-monitor' >/dev/null 2>&1; then
			ko "⛔ la shell ha un --virtual-monitor SUO: il desktop vero NON si vedrebbe"
		else
			ok "⭐ senza --virtual-monitor: il monitor che catturiamo sara' l'unico"
		fi
	else
		ko "gnome-shell non gira per $UTENTE"
		return 1
	fi

	# ⛔ Zero monitor E' il risultato atteso qui, e va DETTO: e' la sessione
	#    «viva, completa e nera» di `gnome.md` §3.1.
	local stato
	stato=$(sudo -u "$UTENTE" env XDG_RUNTIME_DIR="$XDG" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG/bus" \
		gdbus call --session --dest org.gnome.Mutter.DisplayConfig \
		--object-path /org/gnome/Mutter/DisplayConfig \
		--method org.gnome.Mutter.DisplayConfig.GetCurrentState 2>&1)
	if printf '%s' "$stato" | grep -q "^(uint32"; then
		local quanti
		quanti=$(printf '%s' "$stato" | grep -o "'Meta-[0-9]*'" | sort -u | wc -l)
		inf "monitor visti adesso: $quanti"
	else
		ko "GetCurrentState non risponde: $stato"
	fi

	if pgrep -u "$UTENTE" -x pipewire >/dev/null 2>&1; then
		ok "PipeWire gira per $UTENTE"
	else
		ko "PipeWire NON gira per $UTENTE: non ci sara' nessun flusso"
		return 1
	fi
	return 0
}

costruisci()
{
	log "si costruisce (⛔ QUESTO GIRA DENTRO IL CONTENITORE)"
	mkdir -p "$LAV"
	cc -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
		-I"$D" \
		-o "$LAV/04-b26-cursore" \
		"$D/04-b26-cursore.c" "$D/cattura.c" "$D/cursore.c" "$D/registro.c" \
		$(pkg-config --cflags --libs gio-2.0 libpipewire-0.3 libdrm) 2>&1 | head -40
	if [ -x "$LAV/04-b26-cursore" ]; then
		ok "costruito: $LAV/04-b26-cursore"
		return 0
	fi
	ko "non costruito"
	return 1
}

# $1 = --sonda-senza | --sonda-con | --prodotto ; $2 = nome della cartella
gira()
{
	local modo=$1 nome=$2
	local dove="$LAV/$nome"

	log "giro «$nome» — modo $modo"
	rm -rf "$dove"
	mkdir -p "$dove"
	chown -R "$UTENTE" "$dove"

	if [ ! -x "$LAV/04-b26-cursore" ]; then
		ko "il binario non c'e': prima \`costruisci\` (nel contenitore)"
		return 1
	fi

	# ⛔ L'ambiente si compone DA ZERO, una variabile per volta (`CODER.md` §4.5):
	#    regalare l'ambiente di root a una sessione altrui e' il difetto che quella
	#    regola esiste per non avere.
	sudo -u "$UTENTE" env -i \
		HOME="/home/$UTENTE" USER="$UTENTE" LOGNAME="$UTENTE" \
		PATH=/usr/bin:/bin \
		XDG_RUNTIME_DIR="$XDG" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG/bus" \
		"$LAV/04-b26-cursore" "$modo" "$dove" 2>&1 | sed 's/^/    /'
	local esito=${PIPESTATUS[0]}
	inf "uscita del banco: $esito"

	if [ -f "$dove/esiti.jsonl" ]; then
		ok "deposito in $dove"
		ls -la "$dove" | sed 's/^/      /'
	else
		ko "nessun deposito: il banco non ha scritto niente"
	fi
	return $esito
}

# $2 = la cartella del giro `--incorporato`, che e' il CONTROLLO POSITIVO sui
#      pixel della domanda 1.  ⛔ Senza, il giudice lo dice e non conclude.
giudica()
{
	local nome=$1 controllo=${2:-}
	log "il giudizio di «$nome»"
	python3 "$SRC/04-b26-guarda.py" "$LAV/$nome" ${controllo:+"$LAV/$controllo"} 2>&1 | sed 's/^/    /'
	inf "uscita del giudice: ${PIPESTATUS[0]}"
}

case "${1:-tutto}" in
terreno)     porte_intoccabili prima; terreno ;;
costruisci)  costruisci ;;
senza)       gira --sonda-senza senza; giudica senza ;;
con)         gira --sonda-con con;     giudica con ;;
incorporato) gira --incorporato incorporato ;;
prodotto)    gira --prodotto prodotto; giudica prodotto incorporato ;;
tutto)
	porte_intoccabili prima
	terreno || exit 1
	# ⛔ L'ORDINE NON E' CASUALE: prima si fa comparire il difetto, poi si
	#    dimostra che lo strumento sa vedere, e solo alla fine si guarda la cura.
	#    Al contrario, un banco verde non avrebbe mai visto il difetto
	#    (`CODER.md` §3.4).
	gira --sonda-senza senza; giudica senza
	gira --sonda-con con;     giudica con
	# ⛔ IL CONTROLLO POSITIVO DELLA DOMANDA 1 GIRA PRIMA della cura: chiede a
	#    Mutter `cursor-mode = 1` e si prende un fotogramma **col cursore
	#    dentro**.  Serve al giudice per sapere che cosa vale un cursore nei
	#    pixel, altrimenti «non l'ho visto» e «non so guardare» coincidono.
	gira --incorporato incorporato
	gira --prodotto prodotto; giudica prodotto incorporato
	porte_intoccabili dopo
	;;
*)
	ko "modo sconosciuto: ${1:-}"
	exit 2
	;;
esac
