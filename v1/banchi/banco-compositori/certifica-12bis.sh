#!/bin/bash
#
# certifica-12bis.sh — «la RIGA di misura-cattura dichiara la misura che il
# compositore ha DAVVERO negoziato?»
#
#   bash certifica-12bis.sh                       certifica il misuratore in casa
#   bash certifica-12bis.sh --strumento <file>     ne certifica un altro
#                                                  (serve a mettere accanto il
#                                                   binario di ieri e quello di
#                                                   oggi, nello stesso minuto)
#
# ⛔ SI ESEGUE SULL'HOST DI NIC-OS, e DIETRO LA GUARDIA DELLA SESSIONE:
#
#     bash /media/REMOTIX/f21/02-sessione-guardia.sh --etichetta 12bis -- \
#          bash /media/REMOTIX/tmp/banco-compositori/certifica-12bis.sh
#
#   «la sessione e' viva» e «la sessione ha un monitor» sono due domande diverse,
#   e questo banco monta un monitor virtuale SUO accanto a quello della sessione:
#   se la sessione fosse nera, quel che segue misurerebbe il buio e lo direbbe
#   con dei numeri.
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — la voce 12-bis, e il numero giusto sotto l'etichetta falsa
# ===========================================================================
#
# `fasi/00-ambiente.md`, voce 12-bis, 9 agosto 2026: su **labwc** il banco stampo'
# «1920x1080» su una cattura fatta a **1280x720**.  ⛔ E il numero era GIUSTO:
# 61,16, che a 720p e' l'atteso esatto.  Niente sarebbe sembrato storto.  A
# smascherarlo fu `misura-wlroots`, che **stampa la misura vera** invece di
# ripetere l'etichetta ricevuta — uno strumento che non si fida di chi lo chiama.
#
# ⛔ Quella cura a `misura-cattura` non arrivo' mai (difetto **D7**, trovato da
#   F2.2 il 12 agosto 2026): la sua RIGA portava `larghezza`, `altezza` e
#   `colore` presi da argv — cioe' il CHIESTO — mentre il negoziato esisteva,
#   era noto, e finiva solo sullo stderr, che le tabelle non leggono.
#
# ⇒ E' lo strumento con cui la fase 0 ha certificato la macchina: il controllo
#   positivo di tutto il progetto.  Un banco che dichiara una misura non in
#   vigore fa attribuire i numeri **alla scena sbagliata** — la forma d'errore
#   **E2** di `REVIEWER.md` §2, vista dal lato di chi la racconta.
#
# ===========================================================================
# ⛔ LA SCENA, E PERCHE' PROPRIO QUESTA
# ===========================================================================
#
# Serve un caso in cui CHIESTO e NEGOZIATO differiscano davvero.  Con `--mutter`
# non si ottiene: `RecordVirtual` crea il monitor virtuale della misura chiesta,
# e Mutter onora tutto — `[M]` 12 ago 2026, provato da 16x16 a 7680x4320, sette
# misure su sette onorate.  Il caso vero e' un altro, ed e' quello in cui il
# banco viene usato tutti i giorni (`banchi/00-c1-kwin.sh`, `banco-altri.sh`):
#
#   ⭐ ci si aggancia con `--nodo N` a un flusso il cui formato e' GIA' FISSATO
#      da un altro consumatore.  Li' la nostra proposta non filtra piu' niente:
#      PipeWire consegna il formato in vigore, la negoziazione RIESCE, e chi
#      aveva chiesto un'altra misura non se ne accorge.
#
#   A: --mutter --larghezza 1280 --altezza 720          fissa il nodo a 720p
#   B: --nodo <di A> --larghezza 1920 --altezza 1080    chiede 1080p, ottiene 720p
#
# ⚠ E la scena si mette **sul monitor di A, per nome del prodotto**, o B
#   misurerebbe uno schermo su cui non disegna nessuno e il suo zero non
#   distinguerebbe piu' niente.  Sul server i monitor virtuali sono due ed
#   ENTRAMBI 1920x1080: si scelgono per nome, mai per indice ne' per misura
#   (F2.2, «la causa vera»).
#
# ===========================================================================
# ⛔ GLI ATTESI, SCRITTI PRIMA DEL GIRO — e sono TRE, non uno
# ===========================================================================
#
#   P1  controllo positivo   B su un nodo suo (--mutter 1280x720):
#                            RIGA con misura 1280x720 e `onorato` = si
#                            ⇒ senza, il controllo P2 sarebbe verde per sempre,
#                              perche' basterebbe stampare sempre «diverso»
#   P2  il caso vero         B su --nodo di A chiedendo 1920x1080:
#                            RIGA con misura **1280x720** e `onorato` = NO:misura
#   P3  il numero regge      i fotogrammi contati in P2 sono > 0: la misura e'
#                            buona, e' solo di un'altra scena.  ⛔ Uno strumento
#                            che si limitasse a fallire butterebbe via un numero
#                            valido e darebbe un rosso su un compositore sano
#
# Uscite:  0 tutti e tre gli attesi  ·  1 un atteso mancato (il difetto e' vivo)
#          2 il banco non ha potuto misurare (sessione, nodo, scena)
#
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
STRUMENTO=$QUI/misura-cattura
SCENE=$QUI/scene
TMP=${TMP_12BIS:-/media/REMOTIX/tmp/d7}
PRODOTTO_ATTESO="Virtual remote monitor"

# ⛔ La porta e' la 7525, quella assegnata a D7/D8 (`DIFETTI-12-agosto.md`).
#    Questo banco non ne apre nessuna — la riga resta perche' un banco che non
#    nomina la propria porta un giorno ne prende una d'altri.
PORTA=7525

export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=wayland
export LANG=C.UTF-8

while [ $# -gt 0 ]; do
	case "$1" in
	--strumento) STRUMENTO=${2:?serve un file}; shift 2 ;;
	*) echo "uso: $0 [--strumento <file>]" >&2; exit 2 ;;
	esac
done

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

mkdir -p "$TMP"
[ -x "$STRUMENTO" ] || { echo "⛔ manca lo strumento: $STRUMENTO" >&2; exit 2; }
if [ "$QUI/misura-cattura.c" -nt "$STRUMENTO" ] && [ "$STRUMENTO" = "$QUI/misura-cattura" ]; then
	echo "⛔ $STRUMENTO e' PIU' VECCHIO del suo sorgente: ricompila." >&2
	exit 2
fi

PID_A=; PID_SCENA=
pulisci()
{
	[ -n "$PID_SCENA" ] && kill "$PID_SCENA" 2>/dev/null
	[ -n "$PID_A" ] && kill "$PID_A" 2>/dev/null
	wait 2>/dev/null
}
trap pulisci EXIT

# --- il monitor si cerca PER NOME DEL PRODOTTO, mai per indice ---------------
monitor_del_prodotto()
{
	python3 - "$1" <<'PY'
import sys
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

atteso = sys.argv[1]
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
try:
    r = bus.call_sync("org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig",
                      "org.gnome.Mutter.DisplayConfig", "GetCurrentState", None,
                      None, Gio.DBusCallFlags.NONE, 5000, None)
except GLib.Error as err:
    print(f"IGNOTA {err}", file=sys.stderr)
    raise SystemExit(2)
# (serial, monitors, logical_monitors, properties);
# monitor = ((connector, vendor, product, serial), modes, props)
trovati = [m[0][0] for m in r[1] if m[0][2] == atteso]
if len(trovati) != 1:
    print(f"IGNOTA: {len(trovati)} monitor col prodotto «{atteso}» "
          f"(ce ne vuole UNO)", file=sys.stderr)
    raise SystemExit(1)
print(trovati[0])
PY
}

# --- una corsa del misuratore, e la sua RIGA ---------------------------------
riga_di() # $1 = file di uscita
{
	grep '^RIGA' "$1" | head -1
}
campo() # $1 = riga  $2 = numero di campo
{
	printf '%s' "$1" | cut -f"$2"
}

log "certifica-12bis — porta $PORTA · strumento: $STRUMENTO"
inf "impronta: $(md5sum "$STRUMENTO" | cut -d' ' -f1)"

# ===========================================================================
log "P1 — il controllo positivo: su un nodo SUO la misura combacia"
# ===========================================================================
"$STRUMENTO" --mutter --larghezza 1280 --altezza 720 --fps 60 --durata 3 --scarto 1 \
    --etichetta p1-nodo-proprio >"$TMP/p1.out" 2>"$TMP/p1.err"
USCITA_P1=$?
R1=$(riga_di "$TMP/p1.out")
if [ -z "$R1" ]; then
	ko "nessuna RIGA (uscita $USCITA_P1) — il banco non ha potuto misurare"
	sed 's/^/       /' "$TMP/p1.err"
	exit 2
fi
M1=$(campo "$R1" 3)
O1=$(campo "$R1" 25)
inf "misura nella RIGA: $M1   ·   onorato: ${O1:-«la colonna non c'e'»}"
ESITO_P1=1
if [ "$M1" = "1280x720" ] && [ "$O1" = "si" ]; then
	ok "P1: chiesto e negoziato combaciano, e lo strumento lo dice"
	ESITO_P1=0
else
	ko "P1: atteso «1280x720» e onorato «si»"
fi

# ===========================================================================
log "P2 — il caso vero: un nodo il cui formato l'ha gia' fissato un altro"
# ===========================================================================
"$STRUMENTO" --mutter --larghezza 1280 --altezza 720 --fps 60 --durata 40 --scarto 2 \
    --etichetta A-fissa-il-nodo-a-720p >"$TMP/A.out" 2>"$TMP/A.err" &
PID_A=$!
sleep 5
NODO=$(grep -o 'nodo PipeWire [0-9]*' "$TMP/A.err" | grep -o '[0-9]*' | head -1)
if [ -z "$NODO" ]; then
	ko "A non ha montato niente: nessun nodo da riusare"
	sed 's/^/       /' "$TMP/A.err"
	exit 2
fi
inf "A ha fissato il nodo $NODO a $(grep -o 'formato negoziato: [0-9x]*' "$TMP/A.err" | head -1 | awk '{print $3}')"

SCHERMO=$(monitor_del_prodotto "$PRODOTTO_ATTESO")
if [ -z "$SCHERMO" ]; then
	ko "non ho riconosciuto il monitor di A per nome del prodotto"
	exit 2
fi
inf "la scena va sul monitor «$SCHERMO» (prodotto «$PRODOTTO_ATTESO»), scelto per NOME"

if [ ! -s "$SCENE/1920x1080.mp4" ]; then
	ko "manca $SCENE/1920x1080.mp4: 'bash banco.sh prepara'"
	exit 2
fi
stdbuf -oL mpv --no-config --fs --fs-screen-name="$SCHERMO" --loop=inf --no-audio \
    --no-osc --no-input-default-bindings --profile=low-latency \
    "$SCENE/1920x1080.mp4" >"$TMP/scena.log" 2>&1 &
PID_SCENA=$!
sleep 3
if [ -z "$(ps -o stat= -p "$PID_SCENA" | tr -d ' ')" ]; then
	ko "la scena non e' partita — e senza scena lo zero non dice niente"
	sed 's/^/       /' "$TMP/scena.log"
	exit 2
fi

"$STRUMENTO" --nodo "$NODO" --larghezza 1920 --altezza 1080 --fps 60 --durata 6 --scarto 2 \
    --etichetta B-CHIEDE-1920x1080 >"$TMP/p2.out" 2>"$TMP/p2.err"
USCITA_P2=$?
R2=$(riga_di "$TMP/p2.out")
if [ -z "$R2" ]; then
	ko "nessuna RIGA da B (uscita $USCITA_P2)"
	sed 's/^/       /' "$TMP/p2.err"
	exit 2
fi
M2=$(campo "$R2" 3)
C2=$(campo "$R2" 9)
O2=$(campo "$R2" 25)
CH2=$(campo "$R2" 22)
inf "B ha CHIESTO 1920x1080; la sua RIGA dichiara: $M2"
inf "onorato: ${O2:-«la colonna non c'e'»}  ·  misura_chiesta: ${CH2:-«la colonna non c'e'»}"
ESITO_P2=1
if [ "$M2" = "1280x720" ] && [ "$O2" = "NO:misura" ]; then
	ok "P2: la RIGA dichiara la misura NEGOZIATA, e dice che la chiesta non e' stata onorata"
	ESITO_P2=0
elif [ "$M2" = "1920x1080" ]; then
	ko "P2: ⛔ IL DIFETTO E' VIVO — la RIGA dichiara la misura CHIESTA (voce 12-bis)"
else
	ko "P2: atteso «1280x720» con onorato «NO:misura», trovato «$M2» / «${O2:-vuoto}»"
fi

# ===========================================================================
log "P3 — e il numero regge: e' buono, e' solo di un'altra scena"
# ===========================================================================
inf "fotogrammi contati da B: ${C2:-0}   ·   fps: $(campo "$R2" 8)"
ESITO_P3=1
if [ "${C2:-0}" -gt 0 ]; then
	ok "P3: B ha contato ${C2} fotogrammi a 1280x720 — una misura valida, sotto l'etichetta giusta"
	ESITO_P3=0
else
	ko "P3: zero fotogrammi: la scena non arrivava al nodo, e P2 non prova quel che dice"
fi

pulisci; PID_A=; PID_SCENA=

log "Il verdetto"
if [ $ESITO_P1 -eq 0 ] && [ $ESITO_P2 -eq 0 ] && [ $ESITO_P3 -eq 0 ]; then
	ok "VERDE: lo strumento dichiara la misura in vigore, non quella che gli e' stata chiesta"
	exit 0
fi
ko "ROSSO: P1=$ESITO_P1 P2=$ESITO_P2 P3=$ESITO_P3"
exit 1
