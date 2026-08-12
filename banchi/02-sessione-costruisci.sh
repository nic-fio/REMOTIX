#!/bin/bash
#
# 02-sessione-costruisci.sh — il programma minimo che chiama UNA funzione del
# prodotto di P2.1 (`src/sessione.c`) e la mette davanti al banco che la giudica.
#
#   ── da CHUWI, dove sta il deposito ──────────────────────────────────────
#   bash banchi/02-sessione-costruisci.sh qui         compila QUI e basta
#   bash banchi/02-sessione-costruisci.sh porta       manda i sorgenti su NIC-OS
#   bash banchi/02-sessione-costruisci.sh costruisci  compila nel contenitore
#   bash banchi/02-sessione-costruisci.sh certifica   porta + costruisci + ciclo
#
#   ── su NIC-OS, dove vive la sessione ───────────────────────────────────
#   bash .../02-sessione-costruisci.sh ciclo          sano → guasto → risanato
#   bash .../02-sessione-costruisci.sh assicura       chiama sessione_assicura()
#   bash .../02-sessione-costruisci.sh stato          chiama sessione_stato()
#   bash .../02-sessione-costruisci.sh pulisci        toglie le scene del banco
#
# ===========================================================================
# ⛔ PERCHE' ESISTE, VISTO CHE IL BANCO DI F2.1 C'E' GIA'
# ===========================================================================
#
# `banchi/02-sessione-lancia.sh` sa far nascere la sessione col monitor — ma la
# fa nascere **lui**, con `env -i` e un drop-in scritto in bash.  ⇒ Giudica una
# sessione, non giudica il PRODOTTO.  Se il prodotto non scrivesse una riga, quel
# banco resterebbe verde: e' la forma d'errore **E10**, «una prova verde sul
# client sbagliato».
#
# ⭐ Questo file fa la cosa che quello non fa, e solo quella: `CODER.md` §3.6 —
#    *isola UNA funzione sola, e chiamala da fuori*.  Il programma qui sotto ha
#    trenta righe e non fa altro che chiamare `sessione_assicura()`.
#
# ⛔ E il GIUDICE resta quello di F2.1: `02-sessione-stato.py` e
#    `02-sessione-guardia.sh`, non riscritti e nemmeno sfiorati.  Chi si scrive
#    il proprio giudice si assolve da solo.  ⚠ Le loro impronte si CONFRONTANO
#    con quelle del deposito prima di credergli: un giudice diverso da quello che
#    e' stato letto e' un giudice che nessuno ha letto.
#
# ===========================================================================
# ⛔⭐ LA SCENA — «LA CONFIGURAZIONE DICE DI NO», ED E' TUTTO IL PUNTO
# ===========================================================================
#
# L'invariante da dimostrare e' **I7**: *la protezione di un difetto noto sta nel
# programma, non in una riga di configurazione che si puo' perdere*.  Una prova
# fatta su una macchina la cui configurazione **chiede gia'** il monitor non
# dimostrerebbe niente: il monitor ci sarebbe comunque, e il prodotto potrebbe
# non scrivere una riga restando verde.
#
# ⇒ Quindi il ciclo si fa dentro la scena OPPOSTA: si scrive un drop-in
#   `zy-scena-provisioning-perduto.conf` che rimette l'`ExecStart` com'era fino
#   al 12 agosto 2026 — `gnome-shell --headless --no-x11`, **senza**
#   `--virtual-monitor` — cioe' la macchina come sarebbe se `provision-server.sh`
#   §4 non fosse mai passata, o se qualcuno la perdesse di nuovo.
#
#   ⛔ E il prefisso conta: i drop-in di tutte le cartelle si applicano in ordine
#      di NOME FILE.
#          remotix-headless.conf   (in /etc, persistente: CHIEDE il monitor)
#        < zy-scena-…              (la scena di questo banco: NON lo chiede)
#        < zz-remotix-monitor.conf (quello che scrive il PRODOTTO: lo chiede)
#      ⇒ nel giro sano vince il prodotto; nel giro guasto, dove il prodotto non
#        scrive niente, vince la scena.  ⭐ Cosi' la differenza fra 0 e 1 e'
#        **una riga di prodotto**, non una riga di configurazione.
#
#   ⚠ E la scena si IMPONE, non si spera: dopo averla scritta si rilegge
#     l'`ExecStart` in vigore e, se dice ancora `--virtual-monitor`, il banco si
#     ferma.  Un banco che non impone la scena misura la scena di qualcun altro.
#
# ===========================================================================
# ⛔ IL GUASTO — E' IL CODICE DI v1, RIMESSO DOV'ERA
# ===========================================================================
#
# Il guasto non e' inventato: e' `v1/remotix-c/src/sessione.c:671` rimesso in
# piedi su una copia del sorgente,
#
#     if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))
#                ⇩ che sul ramo GNOME vale
#     if (0                        && !scrivi_dropin(larghezza, altezza))
#
# cioe' il corto circuito che faceva entrare `larghezza` e `altezza` nella
# funzione e perderle.  ⛔ E l'innesto si VERIFICA di essere entrato (la
# sostituzione deve aver preso **una** riga, non zero), e il sorgente del
# prodotto si verifica di NON portarlo: un guasto rimasto nell'albero di partenza
# e' gia' costato R12-A.45.
#
# ===========================================================================
# ⛔ QUEL CHE QUESTO BANCO NON TOCCA
# ===========================================================================
#
# La **7448** e la **7501** si contano prima e dopo, e se calano il giro si
# ferma.  Il lucchetto della sessione e' la **7511**, la stessa di F2.1: una
# sessione grafica e' una per utente (I2), e due cicli insieme darebbero due
# misure diverse sotto la stessa etichetta.
#
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(cd "$QUI/.." && pwd)

IND=${IND:-192.168.0.2}
UTE=${UTE:-nicfio}
SSH="ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new $UTE@$IND"
SCP="scp -q -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new"
ENTRA=${ENTRA:-/media/REMOTIX/enter.sh}

# ⛔ Due nomi per lo stesso posto, e si scrivono tutti e due invece di ricavare
#    l'uno dall'altro: `enter.sh` monta /media/REMOTIX su /srv/remotix, e un
#    percorso indovinato un giorno cambia (la lezione di attrezzi-allinea).
LA=${LA:-/media/REMOTIX/tmp/02-sessione}
DENTRO=${DENTRO:-/srv/remotix/tmp/02-sessione}
F21=${F21:-/media/REMOTIX/f21}

MISURA=${MISURA:-1920x1080}
LARG=${MISURA%x*}
ALT=${MISURA#*x}
PORTA_LUCCHETTO=${PORTA_LUCCHETTO:-7511}
PORTE_DA_NON_TOCCARE=${PORTE_DA_NON_TOCCARE:-"7448 7501"}

U=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$U}
DROPIN_DIR=$RUNTIME/systemd/user.control/org.gnome.Shell@wayland.service.d
DROPIN_SCENA=$DROPIN_DIR/zy-scena-provisioning-perduto.conf
DROPIN_PRODOTTO=$DROPIN_DIR/zz-remotix-monitor.conf
DROPIN_F21=$DROPIN_DIR/zz-f21-monitor.conf

ESITI=${ESITI:-$F21/02-sessione-esiti.jsonl}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
att() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ===========================================================================
# Il programma minimo — trenta righe, e non fa altro che chiamare la funzione.
# ===========================================================================
scrivi_programma() # $1 = cartella dove metterlo
{
	cat >"$1/02-sessione-prova.c" <<'FINE'
/*
 * 02-sessione-prova.c — il programma minimo di P2.1.
 *
 * ⛔ Non misura niente e non giudica niente: chiama UNA funzione di
 *    `src/sessione.c` e restituisce il suo numero.  Chi giudica e'
 *    `banchi/02-sessione-stato.py`, che e' di F2.1 e non e' stato toccato.
 *
 * ⭐ Lo stato d'uscita E' `SessioneStato`, cioe' lo stesso alfabeto delle uscite
 *    del banco: 0 SANA · 1 NERA · 2 MISURA · 3 SCELTO DA SE · 4 MORTA · 5 NON
 *    LETTA.  Nessuno deve tradurre, e chi traduce sbaglia.
 *    ⚠ 2 e' anche l'uscita di «non so che verbo mi hai detto», e la differenza
 *      si legge sulla riga stampata: un uso sbagliato non e' una misura.
 */
#include "sessione.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
	const char *verbo = argc > 1 ? argv[1] : "stato";
	unsigned larghezza = 1920, altezza = 1080;
	SessioneMonitor monitor;
	SessioneStato stato;
	bool nata = false;

	if (argc > 2 && sscanf(argv[2], "%ux%u", &larghezza, &altezza) != 2) {
		fprintf(stderr, "⛔ «%s» non e' una misura LxA\n", argv[2]);
		return 2;
	}

	if (strcmp(verbo, "assicura") == 0) {
		stato = sessione_assicura(larghezza, altezza, &nata);
		printf("assicura: %d %s (l'ho fatta nascere io: %s)\n", stato,
		       sessione_marca(stato), nata ? "si" : "no");
		return (int) stato;
	}
	if (strcmp(verbo, "stato") == 0) {
		stato = sessione_stato(larghezza, altezza, &monitor);
		printf("stato: %d %s\n", stato, sessione_marca(stato));
		if (monitor.quanti)
			printf("monitor: %s / %s / %s / %s / %ux%u@%.3f (in tutto %u)\n",
			       monitor.connettore, monitor.fornitore, monitor.prodotto,
			       monitor.seriale, monitor.larghezza, monitor.altezza,
			       monitor.refresh, monitor.quanti);
		return (int) stato;
	}
	if (strcmp(verbo, "viva") == 0) {
		bool viva = sessione_viva();
		printf("viva: %s ⚠ e «viva» NON e' «ha un monitor»\n", viva ? "si" : "no");
		return viva ? 0 : 4;
	}
	if (strcmp(verbo, "termina") == 0) {
		bool andata = sessione_termina();
		printf("termina: %s\n", andata ? "se n'e' andata" : "non se n'e' andata");
		return andata ? 0 : 1;
	}
	fprintf(stderr, "uso: %s {assicura|stato|viva|termina} [LxA]\n", argv[0]);
	return 2;
}
FINE
}

# ===========================================================================
#  Le due copie del sorgente: il PRODOTTO e l'INNESTO (il ramo GNOME di v1)
# ===========================================================================
AGO='if (!scrivi_dropin(larghezza, altezza)) {'
INNESTO='if (0 /* ⛔ INNESTO: il ramo GNOME di v1, sessione.c:671 */ \&\& !scrivi_dropin(larghezza, altezza)) {'

prepara_sorgenti() # $1 = cartella
{
	local d=$1 n
	mkdir -p "$d" || return 1
	cp "$RADICE/src/sessione.c" "$RADICE/src/sessione.h" \
	   "$RADICE/src/registro.c" "$RADICE/src/registro.h" "$d/" || return 1
	scrivi_programma "$d" || return 1

	# ⛔ Il guasto NON deve stare nell'albero di partenza (R12-A.45).
	if grep -q "INNESTO" "$d/sessione.c"; then
		ko "⛔ il sorgente del PRODOTTO porta gia' la parola «INNESTO»:"
		ko "   qualcuno ha lasciato un guasto dentro src/sessione.c.  Non costruisco."
		return 1
	fi
	if ! grep -qF "$AGO" "$d/sessione.c"; then
		ko "⛔ non trovo la riga su cui innestare il guasto:"
		ko "   «$AGO»"
		ko "   Il sorgente e' cambiato e questo banco sta guardando un punto che"
		ko "   non c'e' piu' — un ago ricopiato che smette di trovare qualcosa e"
		ko "   diventa verde e' la lacuna L2."
		return 1
	fi

	sed "s|$AGO|$INNESTO|" "$d/sessione.c" >"$d/sessione-v1.c" || return 1
	n=$(grep -c "INNESTO" "$d/sessione-v1.c")
	if [ "$n" -ne 1 ]; then
		ko "⛔ l'innesto ha preso $n righe invece di 1: un guasto non innestato"
		ko "   darebbe un giro guasto VERDE, che e' la peggiore delle prove."
		return 1
	fi
	ok "sorgenti pronti in $d (innesto verificato: $n riga)"
	return 0
}

# ===========================================================================
#  Il lucchetto sulla 7511 — un DIRITTO A CICLARE, non un ascoltatore.
# ===========================================================================
PID_LUCCHETTO=""
prendi_lucchetto()
{
	python3 -c "
import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
try:
    s.bind(('127.0.0.1', $PORTA_LUCCHETTO))
except OSError as e:
    print('occupata: %s' % e); sys.exit(1)
s.listen(1)
print('preso')
sys.stdout.flush()
time.sleep(86400)
" &
	PID_LUCCHETTO=$!
	sleep 1
	if ! kill -0 "$PID_LUCCHETTO" 2>/dev/null; then
		ko "⛔ la porta $PORTA_LUCCHETTO e' occupata: un'altra copia sta ciclando"
		ko "   la sessione.  Non parto — due cicli insieme darebbero due misure"
		ko "   diverse sotto la stessa etichetta (I2)."
		return 1
	fi
	ok "lucchetto preso sulla $PORTA_LUCCHETTO (pid $PID_LUCCHETTO)"
	return 0
}
molla_lucchetto() { [ -n "$PID_LUCCHETTO" ] && kill "$PID_LUCCHETTO" 2>/dev/null; PID_LUCCHETTO=""; }

conta_ascoltatori() { ss -tuln | grep -c ":$1\b"; }
vicini_prima()
{
	VICINI=""
	for p in $PORTE_DA_NON_TOCCARE; do VICINI="$VICINI $p:$(conta_ascoltatori "$p")"; done
	inf "i vicini che non tocco, prima:$VICINI"
}
vicini_dopo()
{
	local guai=0 p n atteso
	for p in $PORTE_DA_NON_TOCCARE; do
		atteso=$(echo "$VICINI" | tr ' ' '\n' | grep "^$p:" | cut -d: -f2)
		n=$(conta_ascoltatori "$p")
		if [ "$n" -lt "${atteso:-0}" ]; then
			ko "⛔ sulla $p gli ascoltatori sono passati da $atteso a $n: ho toccato"
			ko "   qualcosa che non era mio.  FERMO TUTTO."
			guai=1
		fi
	done
	[ "$guai" -eq 0 ] && ok "i due server voluti sono ancora tutti e due in piedi"
	return $guai
}

# ===========================================================================
#  La scena: «la configurazione ha perso la riga del monitor»
# ===========================================================================
vigore() { systemctl --user show -p ExecStart --value org.gnome.Shell@wayland.service; }

scena_nera()
{
	mkdir -p "$DROPIN_DIR"
	# ⛔ I due `zz-` se ne vanno: se restassero, vincerebbero sulla scena e la
	#    scena non sarebbe imposta.  Quello del prodotto lo riscrivera' il
	#    prodotto, che e' esattamente quel che si vuole misurare.
	rm -f "$DROPIN_PRODOTTO" "$DROPIN_F21"
	cat >"$DROPIN_SCENA" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11
CONF
	systemctl --user daemon-reload || return 1
	local v
	v=$(vigore)
	inf "ExecStart in vigore con la scena: $v"
	case "$v" in
	*--virtual-monitor*)
		ko "⛔ la scena NON e' imposta: qualcuno chiede ancora --virtual-monitor."
		ko "   Non misuro — un banco che non impone la scena misura la scena di"
		ko "   qualcun altro."
		return 1 ;;
	esac
	ok "scena imposta: la configurazione NON chiede il monitor"
	ok "⭐ da qui in poi, se il monitor c'e', l'ha chiesto il PROGRAMMA"
	return 0
}

scena_via()
{
	rm -f "$DROPIN_SCENA" "$DROPIN_PRODOTTO"
	rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
	systemctl --user daemon-reload
	inf "ExecStart in vigore, rimessa la macchina: $(vigore)"
}

# ===========================================================================
#  Il giudice — quello di F2.1, e si controlla che sia quello letto
# ===========================================================================
giudica() # $1 = etichetta
{
	python3 "$F21/02-sessione-stato.py" --attesa "$MISURA" --dal-bus \
	    --etichetta "$1" --esiti "$ESITI"
}

guardia() # $1 = etichetta — le DUE domande separate, davanti a un comando vero
{
	bash "$F21/02-sessione-guardia.sh" --etichetta "$1" -- true
}

impronte_giudici()
{
	local guai=0 f
	for f in 02-sessione-stato.py 02-sessione-guardia.sh; do
		if [ ! -r "$F21/$f" ]; then
			ko "⛔ manca il giudice $F21/$f"; guai=1; continue
		fi
		inf "$(md5sum "$F21/$f")"
	done
	return $guai
}

# ===========================================================================
#  UN GIRO — la sessione si fa NASCERE dal programma, ogni volta
# ===========================================================================
giro() # $1 = binario ; $2 = etichetta ; $3 = atteso ; $4 = atteso guardia
{
	local prog=$1 etichetta=$2 atteso=$3 atteso_g=$4 e g

	log "$etichetta — atteso $atteso ($([ "$atteso" = 0 ] && echo SANA || echo 'NERA: ZERO MONITOR'))"

	# ⛔ Si termina PRIMA: se la sessione fosse gia' sana, `sessione_assicura()`
	#    tornerebbe 0 senza fare niente e il verde sarebbe di chi l'ha fatta
	#    nascere prima — cioe' non del prodotto.
	"$LA/$prog" termina "$MISURA"
	sleep 1

	# ⛔⭐ E LA SCENA SI RIMETTE A OGNI GIRO, NON UNA VOLTA SOLA.
	#
	# Difetto di banco trovato GIRANDO, 12 agosto 2026, ed e' uscito **verde col
	# guasto vivo** — la forma peggiore (`CODER.md` §4.6).  Nella prima stesura
	# la scena si imponeva una volta in testa al ciclo: il giro «sano» faceva
	# scrivere al prodotto il suo `zz-remotix-monitor.conf`, quel file
	# SOPRAVVIVEVA al giro dopo, e il giro «guasto» — che il drop-in non lo
	# scrive per costruzione — nasceva col monitor lasciato dal giro precedente.
	# ⇒ `assicura` diceva **0 SANA** con il codice di v1 dentro, e i tre giudici
	#   dicevano 0 tutti e tre: nessuno mentiva, la scena non era quella
	#   dichiarata.  ⚠ E' la stessa forma di F2.2 il mattino del 12 agosto.
	scena_nera || { ko "⛔ la scena non si e' imposta: non misuro questo giro"; return 1; }

	"$LA/$prog" assicura "$MISURA"
	e=$?
	inf "«$prog assicura» ha detto: $e"

	log "$etichetta — il giudizio del banco di F2.1"
	giudica "P2.1-$etichetta"
	local eg=$?
	inf "02-sessione-stato.py ha detto: $eg"

	log "$etichetta — la guardia (le due domande separate)"
	guardia "P2.1-$etichetta"
	g=$?
	inf "02-sessione-guardia.sh ha detto: $g"

	local falle=0
	[ "$e" -eq "$atteso" ] || { ko "⛔ il prodotto ha detto $e invece di $atteso"; falle=1; }
	[ "$eg" -eq "$atteso" ] || { ko "⛔ il giudice ha detto $eg invece di $atteso"; falle=1; }
	[ "$g" -eq "$atteso_g" ] || { ko "⛔ la guardia ha detto $g invece di $atteso_g"; falle=1; }
	[ "$falle" -eq 0 ] && ok "$etichetta: prodotto $e · giudice $eg · guardia $g, tutti e tre l'atteso"
	return $falle
}

ciclo()
{
	# ⛔ Gli attesi, SCRITTI PRIMA del giro.
	local A_SANO=0 A_GUASTO=1 G_SANO=0 G_GUASTO=71
	log "Gli attesi, scritti PRIMA"
	inf "sano   : prodotto 0 (SANA)              · guardia 0"
	inf "guasto : prodotto 1 (NERA: ZERO MONITOR) · guardia 71 (rifiuta, 70+1)"
	inf "risanato: prodotto 0                     · guardia 0"
	inf "misura chiesta: $MISURA · scena: la configurazione NON chiede il monitor"

	log "I giudici che uso, e le loro impronte"
	impronte_giudici || return 2

	prendi_lucchetto || return 2
	trap 'molla_lucchetto' EXIT
	vicini_prima

	if [ ! -x "$LA/02-sessione-prova" ] || [ ! -x "$LA/02-sessione-prova-v1" ]; then
		ko "⛔ mancano i binari in $LA: si costruiscono da CHUWI con"
		ko "   bash banchi/02-sessione-costruisci.sh costruisci"
		return 2
	fi
	# ⛔ Il binario piu' vecchio del sorgente e' codice diverso da quello letto.
	if [ "$LA/sessione.c" -nt "$LA/02-sessione-prova" ]; then
		ko "⛔ 02-sessione-prova e' piu' VECCHIO di sessione.c: non misuro."
		return 2
	fi

	log "La scena: la configurazione perde la riga del monitor"
	inf "⭐ e si rimette PRIMA DI OGNI GIRO, non solo qui: vedi il riquadro in giro()"
	scena_nera || { scena_via; return 2; }

	local falle=0
	giro 02-sessione-prova    "sano"     0 "$G_SANO"   || falle=$((falle+1))
	giro 02-sessione-prova-v1 "guasto"   1 "$G_GUASTO" || falle=$((falle+1))
	giro 02-sessione-prova    "risanato" 0 "$G_SANO"   || falle=$((falle+1))

	log "Rimetto la macchina come l'ho trovata"
	scena_via
	vicini_dopo || falle=$((falle+1))

	# ⭐ E la si lascia sana per la ragione giusta: la sessione viva adesso e'
	#    quella del giro «risanato», nata dal prodotto.
	log "Come resta la macchina"
	bash "$F21/02-sessione-guardia.sh" --etichetta P2.1-come-resta -- true
	inf "la guardia sulla macchina lasciata: $?"

	if [ "$falle" -eq 0 ]; then
		printf '\n    \033[1;32m⭐ P2.1 E'"'"' CERTIFICATO: sano %s → guasto %s (nel suo punto) → risanato %s\033[0m\n' \
		    "$A_SANO" "$A_GUASTO" "$A_SANO"
		printf '    --  e la differenza fra 0 e 1 e'"'"' UNA RIGA DI PRODOTTO, non una\n'
		printf '        riga di configurazione: la configurazione diceva NO in tutti\n'
		printf '        e tre i giri (I7).\n'
		return 0
	fi
	printf '\n    \033[1;31m⛔ P2.1 NON E'"'"' CERTIFICATO: %s giri non tornano\033[0m\n' "$falle"
	return 1
}

# ===========================================================================
case "${1:-guarda}" in
qui)
	# Compilazione di prova su CHUWI: dice se il modulo compila, e NIENTE altro.
	log "Compilo qui — e questo non e' una misura"
	T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
	prepara_sorgenti "$T" || exit 1
	gcc -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
	    $(pkg-config --cflags gio-2.0) -I"$T" -o "$T/prova" \
	    "$T/02-sessione-prova.c" "$T/sessione.c" "$T/registro.c" \
	    $(pkg-config --libs gio-2.0) || { ko "⛔ il prodotto non compila"; exit 1; }
	gcc -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
	    $(pkg-config --cflags gio-2.0) -I"$T" -o "$T/prova-v1" \
	    "$T/02-sessione-prova.c" "$T/sessione-v1.c" "$T/registro.c" \
	    $(pkg-config --libs gio-2.0) || { ko "⛔ l'innesto non compila"; exit 1; }
	ok "compilano tutti e due (prodotto e innesto)"
	att "⚠ e questo NON dice niente sulla sessione: qui non c'e' GNOME."
	exit 0
	;;
porta)
	log "Porto i sorgenti su NIC-OS"
	T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
	prepara_sorgenti "$T" || exit 1
	cp "$QUI/02-sessione-costruisci.sh" "$T/" || exit 1
	$SSH "mkdir -p $LA" || { ko "⛔ non ho potuto creare $LA"; exit 1; }
	$SCP "$T"/* "$UTE@$IND:$LA/" || { ko "⛔ la copia non e' andata"; exit 1; }
	ok "portati in $LA:"
	$SSH "ls -la $LA"
	exit 0
	;;
costruisci)
	log "Compilo dentro il contenitore"
	# ⛔ MAI UNA REDIREZIONE ATTORNO A `enter.sh`: la richiesta di parola
	#    d'ordine di `sudo` va sullo stderr, e una redirezione la mangia — il
	#    comando resta appeso per sempre, in silenzio.  Dentro le virgolette si',
	#    attorno no.  `fasi/00-ambiente.md` B3.3, pagata cinque volte.
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	if [ -z "$PW" ]; then
		ko "⛔ non ho letto la parola di sudo da ~/SERVER.ssh: non e' «vuota», e'"
		ko "   «non l'ho trovata».  Senza, il comando resterebbe appeso."
		exit 2
	fi
	CFL='-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE'
	printf '%s\n' "$PW" | $SSH "bash $ENTRA \"cd $DENTRO && \
	    gcc $CFL \\\$(pkg-config --cflags gio-2.0) -I. -o 02-sessione-prova \
	        02-sessione-prova.c sessione.c registro.c \\\$(pkg-config --libs gio-2.0) && \
	    gcc $CFL \\\$(pkg-config --cflags gio-2.0) -I. -o 02-sessione-prova-v1 \
	        02-sessione-prova.c sessione-v1.c registro.c \\\$(pkg-config --libs gio-2.0) && \
	    ls -la 02-sessione-prova 02-sessione-prova-v1\""
	e=$?
	[ $e -eq 0 ] && ok "costruiti" || ko "⛔ la costruzione e' fallita (uscita $e)"
	exit $e
	;;
certifica)
	bash "$0" porta || exit $?
	bash "$0" costruisci || exit $?
	log "Il ciclo, su NIC-OS"
	$SSH "bash $LA/02-sessione-costruisci.sh ciclo"
	exit $?
	;;
ciclo)    ciclo; exit $? ;;
assicura) "$LA/02-sessione-prova" assicura "$MISURA"; exit $? ;;
stato)    "$LA/02-sessione-prova" stato "$MISURA"; exit $? ;;
termina)  "$LA/02-sessione-prova" termina "$MISURA"; exit $? ;;
scena-nera)
	# ⛔ La scena «il provisioning ha perso la riga», da sola: serve a misurare a
	#    mano la cura di «viva e nera», che il ciclo non tocca perche' li' la
	#    sessione si ferma sempre prima.
	scena_nera; exit $?
	;;
pulisci)  scena_via; ok "scene del banco tolte"; exit 0 ;;
guarda)
	log "Che cosa c'e', e dove"
	inf "deposito : $RADICE/src/sessione.c"
	inf "su NIC-OS: $LA"
	inf "giudici  : $F21/02-sessione-stato.py, $F21/02-sessione-guardia.sh"
	$SSH "ls -la $LA 2>&1 | tail -n +2"
	exit 0
	;;
*)
	echo "uso: $0 {qui|porta|costruisci|certifica|ciclo|assicura|stato|termina|pulisci|guarda}" >&2
	exit 2
	;;
esac
