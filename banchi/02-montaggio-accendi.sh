#!/bin/bash
#
# 02-montaggio-accendi.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** DAL
# CONTENITORE, e questa riga e' la decisione piu' importante del file.
#
#   bash /media/REMOTIX/src/02-montaggio-accendi.sh stato
#   bash /media/REMOTIX/src/02-montaggio-accendi.sh accendi
#   bash /media/REMOTIX/src/02-montaggio-accendi.sh spegni
#   bash /media/REMOTIX/src/02-montaggio-accendi.sh riaccendi
#
# ===========================================================================
# ⛔⭐ PERCHE' FUORI DAL CONTENITORE — la `[?]` 1 di `P2-1-sessione.md` §8,
#     chiusa il 12 agosto 2026 con una misura e non con una preferenza.
#
# Il server di casa (7448) gira **dentro** il chroot di `enter.sh`.  Quel
# chroot monta `/proc`, `/sys`, `/dev` e `/srv/src` — ⛔ e **non** `/run`.
# `[M]` 12 agosto 2026: `/media/REMOTIX/devroot/run/user` **non esiste**.
#
# Li' dentro, quindi:
#
#   /run/user/1000/bus         il bus di sessione di GNOME   ⛔ non c'e'
#   /run/user/1000/pipewire-0  il flusso dei fotogrammi      ⛔ non c'e'
#   /run/user/1000/systemd     il gestore d'utente           ⛔ non c'e'
#
# ⇒ Tutti e tre gli anelli che la fase 2 aggiunge — `sessione.c`, `mutter.c`,
#   `cattura.c` — parlano con qualcosa che dentro il contenitore **non esiste**.
#   `sessione_assicura()` uscirebbe **5 NON LETTA** (non «zero monitor»: non ho
#   potuto guardare, che e' un fatto diverso), `mutter_apri()` fallirebbe, e il
#   server partirebbe senza un pixel da mostrare — dichiarandolo, ma senza.
#
# ⚠ E NON e' un difetto del contenitore: il contenitore esiste per COSTRUIRE
#   (ci stanno ngtcp2 1.25 e nghttp3 1.18, che i pacchetti non danno).  Il
#   prodotto vero girera' accanto alla sessione grafica dell'utente, che e'
#   esattamente quel che fa questo file.
#
# ⭐ E il binario e' LO STESSO: `[M]` 12 agosto 2026 l'host e' Debian 13
#    (glibc 2.41-12+deb13u3), lo stesso del chroot.  Non si ricompila niente e
#    non si costruisce un secondo prodotto — ⛔ che sarebbe la forma d'errore
#    peggiore: due binari sotto la stessa etichetta.
#
# ⛔ Quel che cambia sono **le librerie da cercare**: `remotix` e' collegato a
#    `ngtcp2` 1.25 costruito in `/srv/src/b2/...`, che sull'host si chiama
#    `/media/REMOTIX/src/b2/...`.  ⚠ Senza `LD_LIBRARY_PATH` il caricatore
#    trova la `libngtcp2.so.16` **dei pacchetti** (1.11): stesso soname, altra
#    libreria — e il sintomo non sarebbe un errore di caricamento, sarebbe una
#    stretta di mano che si comporta in modo diverso.  ⇒ Si dichiara, e si
#    VERIFICA con `ldd` prima di accendere.
#
# ===========================================================================
# ⛔ LA PORTA E' LA 7561, ED E' DI QUESTO GIRO
#
# 7448 (il prodotto di casa) e 7501 (il bersaglio di P5) **non si toccano**:
# si contano prima e dopo, e devono restare come sono.  ⚠ E ban-file, socket
# del comando e certificati sono PROPRI: due server che condividessero il file
# dei ban si banerebbero a vicenda (`MEMORY.md`, banchi in parallelo).
#
# ===========================================================================
# ⛔ L'UTENTE CON CUI SI ENTRA E' `nicfio`, E LA RAGIONE E' PAM
#
# `[M]`: sull'host non esistono ne' `prova` ne' `prova2` — sono utenti del
# chroot.  E il server gira come `nicfio` (uid 1000), non come root, perche' e'
# l'uid che possiede il bus di sessione e il socket di PipeWire.
#
# ⚠ Da cui una conseguenza che va detta invece di scoprirla: `pam_unix` fuori
#   da root passa da `unix_chkpwd`, che verifica **solo la parola d'ordine di
#   chi lo invoca**.  ⇒ Da qui si autentica `nicfio` e nessun altro, ed e'
#   abbastanza per la fase 2 — ma NON e' il regime del prodotto, che girera'
#   da root o come unita' di sistema.  Dichiarato, non nascosto.
#
set -uo pipefail

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7561}
D=${D:-/media/REMOTIX/src/remotix}
LAV=${LAV:-/media/REMOTIX/tmp/02-montaggio}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
RILIEVO=$LAV/rilievo
LOG=$LAV/registro.log
PIDF=$LAV/pid

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

impronta() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

mio_pid()
{
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--porta $PORTA" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ I due server che NON sono miei si contano prima e dopo: se calano, il
#    giro ha fatto un danno, e un danno che nessuno conta non e' successo.
vicini()
{
	local a b
	a=$(ss -tuln 2>/dev/null | grep -c ':7448\b')
	b=$(ss -tuln 2>/dev/null | grep -c ':7501\b')
	printf '7448: %s ascoltatori · 7501: %s ascoltatori\n' "$a" "$b"
}

case "${1:-stato}" in
stato)
	log "Il server del montaggio, sulla $PORTA"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then
		ko "nessun server sulla $PORTA"
		[ -x "$D/remotix" ] && inf "sul disco: $(impronta "$D/remotix")…"
		exit 1
	fi
	disco=$(impronta "$D/remotix")
	vivo=$(impronta "/proc/$pid/exe")
	inf "pid $pid, acceso il $(ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^ *//')"
	inf "exe: $(readlink "/proc/$pid/exe" 2>/dev/null || echo '⛔ non leggibile')"
	inf "in esecuzione: ${vivo:-⛔ non leggibile}  ·  sul disco: ${disco:-⛔ manca}"
	if [ -z "$vivo" ]; then
		ko "⛔ non ho potuto leggere il binario in esecuzione: NON dico che combacia"
		exit 2
	fi
	if [ "$vivo" = "$disco" ]; then
		ok "⭐ sta eseguendo il binario che c'e' sul disco"
		exit 0
	fi
	ko "⛔ STA ESEGUENDO UN ALTRO BINARIO — cura: bash $0 riaccendi"
	exit 3 ;;
spegni)
	log "Spengo"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then ok "non c'era niente acceso sulla $PORTA"; exit 0; fi
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { ko "il pid $pid non e' morto"; exit 3; }
	rm -f "$PIDF"
	ok "spento (pid $pid)"
	inf "$(vicini)"
	exit 0 ;;
accendi) ;;
riaccendi) bash "$0" spegni || exit 3 ;;
*) echo "uso: $0 [stato|accendi|spegni|riaccendi]"; exit 2 ;;
esac

# --- accendi ---------------------------------------------------------------
log "0. Il terreno, dichiarato prima di toccarlo"
inf "$(vicini)"
inf "binario: $D/remotix  ($(impronta "$D/remotix")…)"
inf "cartella di lavoro: $LAV"
[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }

command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
[ "$n" -eq 0 ] || { ko "⛔ la porta $PORTA e' gia' occupata ($n righe): spegni prima"; exit 2; }

mkdir -p "$CERT" "$RILIEVO" || { ko "⛔ non ho potuto preparare $LAV"; exit 2; }

log "1. ⛔ Le librerie: quelle costruite, non quelle dei pacchetti"
export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if ! ldd "$D/remotix" > "$LAV/ldd.txt" 2>&1; then
	ko "⛔ ldd non ha finito: non dico che le librerie ci sono"
	exit 2
fi
if grep -q 'not found' "$LAV/ldd.txt"; then
	ko "⛔ manca almeno una libreria:"
	grep 'not found' "$LAV/ldd.txt" | sed 's/^/        /'
	exit 2
fi
for l in libngtcp2 libnghttp3; do
	riga=$(grep -m1 "$l" "$LAV/ldd.txt")
	case "$riga" in
	*"$LAV"*|*/media/REMOTIX/src/b2/*) ok "$l ← $(printf '%s' "$riga" | sed 's/^[[:space:]]*//')" ;;
	*)  ko "⛔ $l NON viene dall'albero costruito: $(printf '%s' "$riga" | sed 's/^[[:space:]]*//')"
	    ko "   E' la libreria dei pacchetti — stesso soname, altra libreria."
	    exit 2 ;;
	esac
done
# ⭐ E le tre della fase 2 si dichiarano: se una mancasse il server non
#    partirebbe affatto, e il sintomo sarebbe «non si accende».
for l in libpipewire libavcodec libswscale libgio; do
	riga=$(grep -m1 "$l" "$LAV/ldd.txt")
	[ -n "$riga" ] && inf "$(printf '%s' "$riga" | sed 's/^[[:space:]]*//')"
done

log "2. ⛔ Il servizio PAM sull'host"
if [ -f /etc/pam.d/remotix ]; then
	ok "/etc/pam.d/remotix c'e'"
else
	ko "⛔ /etc/pam.d/remotix NON C'E': PAM ripieghera' su «other», che su"
	ko "   Debian e' pam_deny — OGNI parola d'ordine giusta sara' rifiutata e"
	ko "   l'utente leggera' «utente o parola d'ordine non corretti».  Cura:"
	ko "     sudo cp $D/remotix.pam /etc/pam.d/remotix"
	exit 2
fi

log "3. La sessione grafica, chiesta PRIMA di accendere"
if [ -S /run/user/1000/bus ] && [ -S /run/user/1000/pipewire-0 ]; then
	ok "bus di sessione e socket di PipeWire ci sono (e' per questo che si gira qui)"
else
	ko "⛔ /run/user/1000/bus o pipewire-0 non ci sono: qui non c'e' niente da"
	ko "   catturare, e il server partirebbe senza dirlo prima"
	exit 2
fi

log "4. Accendo"
# ⛔ Il registro si apre IN CODA, mai troncato: troncare un registro che un
#    processo tiene aperto ci scava dentro un buco di NUL che acceca ogni grep.
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban-file "$BAN" --comando-socket "$SOCK" \
      --rilievo "$RILIEVO" \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ Marcatori, non `sleep`: «il processo e' vivo» e «la porta risponde» sono
#    due fatti diversi.  ⚠ E qui il primo fotogramma si prende PRIMA degli
#    ascoltatori, quindi l'attesa e' piu' lunga di quella di casa: cattura
#    (fino a 5 s) piu' due codifiche (`[M]` 306 e 99-390 ms).
g=0
while [ "$g" -lt 120 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	ko "⛔ il server e' morto subito.  Le ultime righe del registro:"
	tail -20 "$LOG" | sed 's/^/        /'
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	ko "⛔ pid $pid vivo ma su :$PORTA ci sono $righe ascoltatori: §2.4 ne vuole DUE"
	tail -20 "$LOG" | sed 's/^/        /'
	exit 3
fi
ok "acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s"

log "5. ⭐ Che cosa ha detto del video — e questa e' la misura, non l'accensione"
# ⚠ Il registro non ha parentesi: `registro.c` scrive «HH:MM:SS.mmm area  …».
#   Un `grep` su una forma inventata sarebbe muto e sembrerebbe «non ha detto
#   niente sul video» — la forma E8 dentro lo strumento che la deve trovare.
grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (video|sessione) ' "$LOG" \
	| tail -25 | sed 's/^/        /'
inf "$(vicini)"
inf "il rilievo (fotogramma catturato e flussi) sta in $RILIEVO"
ls -la "$RILIEVO" 2>/dev/null | sed 's/^/        /'
exec bash "$0" stato
