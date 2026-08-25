#!/bin/bash
#
# 01-casa-7448.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Il «server di casa»: il
# PRODOTTO sulla porta 7448, quello che gli altri banchi trovano acceso.
#
#   bash /srv/src/01-casa-7448.sh stato      chi gira, e su che binario
#   bash /srv/src/01-casa-7448.sh costruisci ricostruisce dai sorgenti di adesso
#   bash /srv/src/01-casa-7448.sh accendi
#   bash /srv/src/01-casa-7448.sh spegni
#   bash /srv/src/01-casa-7448.sh riaccendi  costruisci + spegni + accendi
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — «IL SERVER E' ACCESO» NON DICE SU CHE COSA
#
# `[M]` la notte fra l'11 e il 12 agosto 2026: il server di casa girava **dalle
# 08:28** e il binario sul disco era delle **17:26**.  `readlink /proc/PID/exe`
# diceva `/srv/src/remotix/remotix (deleted)`, e le due impronte erano diverse —
# `53c46311…` in esecuzione contro `abc021cf…` sul disco.  ⇒ Per tredici ore
# chiunque avesse interrogato la 7448 avrebbe misurato **il prodotto senza le
# cure del congedo**, credendo di misurare quello curato.
#
# ⚠ E nessuno se n'era accorto perche' la riga di comando era stata battuta a
#   mano: non c'era nessun file da rileggere, e «e' acceso» sembrava una
#   risposta completa.  E' la stessa forma dell'innesto disallineato della
#   stessa notte (`attrezzi-allinea-innesto.sh`) e della trappola gia' pagata
#   su B11 — *«il file c'e'» e «il file e' quello che ho appena costruito» sono
#   due domande diverse* (`LEZIONI.md` §1.9 punto 8).
#
# ⭐ Da cui `stato`, che non chiede «e' vivo?» ma **«sta eseguendo il binario
#    che c'e' sul disco?»**, e lo dice confrontando le due impronte.
#
# ---------------------------------------------------------------------------
# ⛔ LA RIGA DI COMANDO E' QUELLA CHE GIRAVA, COPIATA DA `/proc/PID/cmdline`
#
# Non ricostruita a memoria: letta dal processo vivo prima di ammazzarlo, il
# 12 agosto 2026.  ⚠ In particolare `--pagina` qui **si usa** (a differenza di
# `01-p5-accendi.sh`, che accende da dentro la cartella apposta): cambiarlo
# cambierebbe la scena che gli altri banchi si aspettano.
#
# ⛔ E IL REGISTRO SI APRE IN CODA (`>>`), MAI TRONCATO: troncare un registro
#    che un processo tiene aperto ci scava dentro un buco di NUL che acceca
#    ogni `grep` (`LEZIONI.md` §1.9 punto 9, pagata la stessa notte).
set -uo pipefail

D=${D:-/srv/src/remotix}
GEMELLO=${GEMELLO:-/srv/src/rcp}
PORTA=${PORTA:-7448}
IND=${IND:-192.168.0.2}

CERT=/srv/src/remotix-cert
BAN=/srv/src/remotix-ban
SOCK=/srv/src/b8-comando.sock
LOG=/srv/src/remotix-browser.log
PIDF=/srv/src/remotix-casa.pid

# ⛔ Il PID non si cerca con `pgrep -f remotix`: porterebbe via i server degli
#    altri giri (la 7501 di P5, la 7481 di B13).  Si cerca la porta.
mio_pid()
{
	local p
	# ⭐ Prima il file, che e' un fatto scritto; poi la riga di comando, per i
	#    server accesi a mano prima che questo file esistesse.
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--porta $PORTA" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

impronta() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

case "${1:-stato}" in
stato)
	if ! pid=$(mio_pid); then
		echo "--  nessun server sulla $PORTA"
		[ -x "$D/remotix" ] && echo "--  sul disco: $(impronta "$D/remotix")…  $(stat -c '%y' "$D/remotix" | cut -c1-16)"
		exit 1
	fi
	disco=$(impronta "$D/remotix")
	vivo=$(impronta "/proc/$pid/exe")
	echo "--  pid $pid, acceso il $(ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^ *//')"
	echo "--  exe: $(readlink "/proc/$pid/exe" 2>/dev/null || echo '⛔ non leggibile: serve root')"
	echo "--  in esecuzione: ${vivo:-⛔ non leggibile}   ·   sul disco: ${disco:-⛔ manca}"
	if [ -z "$vivo" ]; then
		echo "NO  ⛔ non ho potuto leggere il binario in esecuzione: NON dico che combacia"
		exit 2
	fi
	if [ "$vivo" = "$disco" ]; then
		echo "OK  ⭐ sta eseguendo il binario che c'e' sul disco"
		exit 0
	fi
	echo "NO  ⛔ STA ESEGUENDO UN ALTRO BINARIO: chi interroga la $PORTA misura"
	echo "    un prodotto diverso da quello che i sorgenti dicono.  Cura:"
	echo "      bash $0 riaccendi"
	exit 3 ;;
costruisci)
	[ -d "$D" ] || { echo "NO  ⛔ $D non c'e'"; exit 2; }
	# ⛔ Si guarda l'ESITO del costruttore, non la presenza del binario dopo
	#    (LEZIONI.md §1.9 punto 8).
	( cd "$D" && GEMELLO="$GEMELLO" bash costruisci.sh ) || {
		echo "NO  ⛔ la costruzione e' FALLITA: non spengo niente, e il server"
		echo "    che gira resta quello di prima — che almeno si sa qual e'"
		exit 3
	}
	echo "OK  costruito: $(impronta "$D/remotix")…"
	exit 0 ;;
spegni)
	if ! pid=$(mio_pid); then echo "--  non c'era niente acceso sulla $PORTA"; exit 0; fi
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { echo "NO  ⛔ il pid $pid non e' morto"; exit 3; }
	rm -f "$PIDF"
	echo "OK  spento (pid $pid)"
	exit 0 ;;
accendi) ;;
riaccendi)
	bash "$0" costruisci || exit 3
	bash "$0" spegni     || exit 3
	;;
*) echo "uso: $0 [stato|costruisci|accendi|spegni|riaccendi]"; exit 2 ;;
esac

# --- accendi ---------------------------------------------------------------
command -v ss >/dev/null || { echo "NO  ⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ la porta $PORTA e' gia' occupata ($n righe): spegni prima"
	exit 2
fi
[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix non c'e': manca il passo «costruisci»"; exit 2; }
[ -f "$D/pagina.html" ] || { echo "NO  ⛔ $D/pagina.html non c'e'"; exit 2; }

# ⛔ La riga di comando e' quella letta da /proc/PID/cmdline del server che
#    girava: non si "migliora" qui, o la scena degli altri banchi cambia.
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban "$BAN" --comando-socket "$SOCK" \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ B0.7: marcatori, non `sleep`.  «Il processo e' vivo» e «la porta risponde»
#    sono due fatti diversi, e a chi arriva dopo serve il secondo.
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ il server e' morto subito.  Le ultime righe del registro:"
	tail -5 "$LOG" | sed 's/^/        /'
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	echo "NO  ⛔ pid $pid vivo ma su :$PORTA ci sono $righe ascoltatori: §2.4 ne vuole DUE"
	tail -5 "$LOG" | sed 's/^/        /'
	exit 3
fi
echo "OK  acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s"
exec bash "$0" stato
