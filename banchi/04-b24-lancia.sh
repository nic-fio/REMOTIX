#!/bin/bash
#
# 04-b24-lancia.sh — B24: l'input arriva DAVVERO al desktop?  Anello A4, fase 4.
#
#   bash 04-b24-lancia.sh            la misura intera
#   bash 04-b24-lancia.sh --pulisci  spegne quel che fosse rimasto acceso
#
# ⚠ GIRA SUL SERVER (192.168.0.2), come utente `nicfio`, e diventa `prova` per
#   entrare nella SUA sessione GNOME — l'unica dove il desktop vero si vede
#   (`fasi/rapporti/F5-desktop-vero.md`, decisione del 14 agosto 2026).
#
# ---------------------------------------------------------------------------
# ⛔⛔ SI VERIFICA DAL LATO CHE **RICEVE** — `CODER.md` §3.8
#
# L'iniettore stampa «punta 800 450 -> 0».  Quello e' il registro di chi manda:
# dice che abbiamo chiamato una funzione, **non** che il desktop ha ricevuto
# qualcosa.  Il verdetto lo da' `04-b24-testimone`, che e' **una finestra vera**
# aperta dentro la sessione, sul monitor che l'iniettore ha montato, e che
# stampa una riga per ogni evento che il compositore le consegna.
#
# ---------------------------------------------------------------------------
# ⚠ IL TESTIMONE ERA UN BROWSER, E IL BROWSER NON HA FUNZIONATO — `[M]` 14 ago
#
# Il banco S7 misurava il segno della rotella su `deltaY` di una pagina in
# Firefox `--kiosk`.  Qui Firefox **parte e non chiede mai la pagina**: processo
# vivo, stato `S`, ⛔ zero richieste HTTP dopo 149 s, registro vuoto.  Provato
# con profilo nuovo e riusato, con e senza terminale, tre giri.  ⚠ La causa non
# e' stata trovata: sta in «che cosa NON ha funzionato» del rapporto.
#
# ⇒ Il testimone e' diventato una finestra Wayland nostra.  ⭐ Ed e' PIU' vicino
#   alla verita', non un ripiego peggiore: fra `libei` e la pagina c'erano
#   Mutter **e** il browser; qui c'e' solo Mutter.
#
# ---------------------------------------------------------------------------
# ⛔ IL MONITOR SI SCEGLIE PER MISURA, NON SI SPERA — forma E2
#
# La sessione di `prova` puo' avere gia' un monitor di un altro client.  Il
# nostro `RecordVirtual` ne monta un altro, e ⛔ se il testimone finisse su
# quello sbagliato ogni iniezione andrebbe dove nessuno guarda.  ⇒ Il nostro si
# chiede di una misura DIVERSA (1600x900), e il testimone si mette a schermo
# intero **su quel `wl_output`**, uscendo con un errore se non c'e'.
#
# ---------------------------------------------------------------------------
# ⛔ L'ORDINE FRA INIETTORE E TESTIMONE, `[M]` 10 agosto 2026 (banco S7)
#
#   testimone PRIMA dell'iniettore  ⇒ non arriva NIENTE;
#   iniettore PRIMA del testimone   ⇒ arriva tutto.
#
# La spiegazione resta `[?]`.  L'ordine e' `[M]`, e qui si rispetta.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
TELA=${TELA:-1600x900}
LARG=${TELA%x*}
ALT=${TELA#*x}
UTENTE=${UTENTE:-prova}
UID_P=${UID_P:-1001}
PAROLA=${PAROLA:-nicfio}
LAVORO=/tmp/04-b24
BIN=$LAVORO/04-b24-iniezione
TEST=$LAVORO/04-b24-testimone
VISTO=$LAVORO/04-b24-visto.jsonl
E=/media/REMOTIX/enter.sh
DENTRO=/srv/src/04-b24-src
FUORI=/media/REMOTIX/src/04-b24-src

log()   { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()    { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()    { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
dubbio(){ printf '    \033[1;33m??\033[0m  %s\n' "$*"; }
inf()   { printf '    --  %s\n' "$*"; }
ESITO=0

# ⛔ LA PAROLA D'ORDINE — ne' su `argv` ne' appesa al marcatempo di `sudo`.
#    `printf … | sudo -S …` si rompe appena il comando ha una redirezione
#    addosso (la fifo prende il posto della pipe), e `sudo -v` una volta sola
#    non regge tre passi piu' in la' `[M]` 14 ago 2026.  ⇒ `SUDO_ASKPASS`, con
#    la parola in un file 0600 scritto da un builtin.
ASKPASS=$(mktemp); PAROLA_FILE=$(mktemp)
chmod 700 "$ASKPASS"; chmod 600 "$PAROLA_FILE"
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"
printf '#!/bin/sh\ncat %s\n' "$PAROLA_FILE" > "$ASKPASS"
export SUDO_ASKPASS="$ASKPASS"

come_prova()
{
	sudo -A -u "$UTENTE" \
	    env XDG_RUNTIME_DIR=/run/user/$UID_P \
	        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID_P/bus \
	        WAYLAND_DISPLAY=wayland-0 \
	        HOME=/home/$UTENTE USER=$UTENTE LANG=C.UTF-8 \
	        "$@"
}

if ! sudo -A true 2>/dev/null; then
	printf '⛔ la parola d ordine di sudo non e stata accettata: il banco non parte\n'
	exit 2
fi

spegni_tutto()
{
	sudo -A pkill -f 04-b24-iniezione 2>/dev/null
	sudo -A pkill -f 04-b24-testimone 2>/dev/null
	sudo -A pkill -u "$UID_P" -f firefox 2>/dev/null
}

if [ "${1:-}" = --pulisci ]; then
	spegni_tutto
	printf 'spento quel che c era\n'
	exit 0
fi

congedo()
{
	printf '\n\033[1m== Il congedo\033[0m\n'
	exec 9>&- 2>/dev/null
	spegni_tutto
	rm -f "$ASKPASS" "$PAROLA_FILE" "$FUORI/input-guasto.c"
	inf "quel che il testimone ha visto: $VISTO"
	inf "quel che l'iniettore ha detto:  $LAVORO/iniettore.log"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "0. Lo stato iniziale, DICHIARATO (B0.1)"

if ! pgrep -u "$UID_P" -x gnome-shell >/dev/null; then
	ko "l'utente $UTENTE non ha una sessione GNOME viva: la misura non comincia"
	exit 2
fi
inf "gnome-shell di $UTENTE: $(tr '\0' ' ' < "/proc/$(pgrep -u "$UID_P" -x gnome-shell | head -1)/cmdline")"
MON_PRIMA=$(come_prova gdbus call --session -d org.gnome.Mutter.DisplayConfig \
    -o /org/gnome/Mutter/DisplayConfig \
    -m org.gnome.Mutter.DisplayConfig.GetCurrentState 2>/dev/null | grep -o "'Meta-[0-9]*'" | sort -u | tr '\n' ' ')
inf "monitor PRIMA: ${MON_PRIMA:-nessuno}"
# ⛔ E si spegne quel che e' rimasto acceso dal giro di prima: un superstite che
#    tiene una porta o un lucchetto fa fallire il nuovo e ACCUSA la cosa
#    sbagliata (`[M]` 14 ago 2026, e costava un giro ogni volta).
spegni_tutto
sleep 2

# ---------------------------------------------------------------------------
log "1. I due programmi, compilati nel devroot"

# ---------------------------------------------------------------------------
# ⛔⛔ IL GUASTO INNESTATO — `CODER.md` §3.3: il banco si certifica PRIMA di
#     crederlo, e certificare vuol dire **fargli vedere il difetto**.
#
#   GUASTO=segno   toglie il meno da `input_rotella` in una COPIA di `input.c`
#                  ⇒ il banco DEVE diventare rosso sul segno della rotella.
#   GUASTO=conto   fa ritornare 0 a `input_rilascia_tutto` senza rilasciare
#                  ⇒ il banco DEVE accorgersene, e dal lato che riceve.
#
# ⛔ Si tocca una COPIA (`input-guasto.c`), mai `src/input.c`: un guasto che
#    sopravvive alla prova e' la cosa peggiore che un banco possa lasciare.
SORGENTE_INPUT=input.c
if [ -n "${GUASTO:-}" ]; then
	cp "$FUORI/input.c" "$FUORI/input-guasto.c"
	case "$GUASTO" in
	segno)
		sed -i 's|(double) -asse_y / UNITA_PER_DELTA|(double) asse_y / UNITA_PER_DELTA|' \
		    "$FUORI/input-guasto.c" ;;
	conto)
		sed -i 's|^\tfor (uint32_t c = 0; c < MAX_TASTO; c++)|\treturn 0;\n\tfor (uint32_t c = 0; c < MAX_TASTO; c++)|' \
		    "$FUORI/input-guasto.c" ;;
	*) printf '⛔ GUASTO ignoto: «%s»\n' "$GUASTO"; exit 2 ;;
	esac
	if cmp -s "$FUORI/input.c" "$FUORI/input-guasto.c"; then
		printf '⛔ IL GUASTO «%s» NON HA CAMBIATO NIENTE: la certificazione non vale\n' "$GUASTO"
		exit 2
	fi
	SORGENTE_INPUT=input-guasto.c
	printf '\n\033[1;33m⛔ GIRO DI CERTIFICAZIONE, con il guasto «%s» innestato.\033[0m\n' "$GUASTO"
	printf '   Il banco DEVE diventare ROSSO.  Se resta verde, non sa vedere il difetto.\n'
fi

printf '%s\n' "$PAROLA" | bash "$E" --root "cd $DENTRO && \
  wayland-scanner client-header /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-client-protocol.h && \
  wayland-scanner private-code  /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-protocol.c && \
  gcc -O1 -g -Wall -o 04-b24-iniezione 04-b24-iniezione.c $SORGENTE_INPUT mutter.c tastiera.c registro.c \$(pkg-config --cflags --libs libei-1.0 xkbcommon gio-2.0 gio-unix-2.0 libpipewire-0.3) && \
  gcc -O1 -g -Wall -o 04-b24-testimone 04-b24-testimone.c xdg-shell-protocol.c \$(pkg-config --cflags --libs wayland-client)"
for f in 04-b24-iniezione 04-b24-testimone; do
	if [ ! -x "$FUORI/$f" ]; then ko "$f non si e' compilato"; exit 3; fi
done
mkdir -p "$LAVORO" && chmod 777 "$LAVORO"
cp "$FUORI/04-b24-iniezione" "$FUORI/04-b24-testimone" "$LAVORO/"
chmod 755 "$BIN" "$TEST"
ok "iniettore e testimone in $LAVORO"

# ---------------------------------------------------------------------------
log "2. L'iniettore — PRIMA del testimone, ed e' l'ordine misurato"

mkfifo "$LAVORO/comandi.$$" 2>/dev/null
chmod 666 "$LAVORO/comandi.$$"
come_prova "$BIN" --tela "$TELA" <"$LAVORO/comandi.$$" >"$LAVORO/iniettore.log" 2>&1 &
exec 9>"$LAVORO/comandi.$$"
rm -f "$LAVORO/comandi.$$"
manda() { printf '%s\n' "$*" >&9; }

i=0
while [ $i -lt 60 ]; do
	grep -qx "B24: PRONTO" "$LAVORO/iniettore.log" 2>/dev/null && break
	grep -q "B24: ERRORE" "$LAVORO/iniettore.log" 2>/dev/null && break
	sleep 1; i=$((i + 1))
done
if ! grep -qx "B24: PRONTO" "$LAVORO/iniettore.log" 2>/dev/null; then
	ko "l'iniettore non e' arrivato a PRONTO in 60 s:"
	tail -30 "$LAVORO/iniettore.log" | sed 's/^/        /'
	exit 4
fi
ok "iniettore PRONTO"
grep -E "mapping-id|MONITOR|regione del puntatore|flusso attivo|RIPIEGO" "$LAVORO/iniettore.log" \
    | sed 's/^/        /'

# ⭐ LA TESI 4, MISURATA: i due mapping-id, e quale porta la regione.
NOSTRO=$(sed -n 's/.*DICHIARATO da noi a RecordVirtual: «\(.*\)».*/\1/p' "$LAVORO/iniettore.log" | head -1)
SUO=$(sed -n 's/.*PUBBLICATO da Mutter nei Parameters: «\(.*\)».*/\1/p' "$LAVORO/iniettore.log" | head -1)
if [ -n "$NOSTRO" ] && [ -n "$SUO" ] && [ "$NOSTRO" != "$SUO" ]; then
	ok "il mapping-id che DICHIARIAMO e quello che Mutter PUBBLICA sono DIVERSI:"
	inf "   nostro «$NOSTRO»  ≠  suo «$SUO»"
	if grep -q "regione del puntatore per chiave" "$LAVORO/iniettore.log"; then
		ok "e la regione si riconosce per CHIAVE, cioe' con quello di Mutter"
	else
		ko "la regione NON si e' riconosciuta per chiave: si e' ripiegato su un altro criterio"
	fi
else
	ko "i due mapping-id non si sono letti, o sono uguali: «$NOSTRO» / «$SUO»"
fi

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
righe() { wc -l < "$VISTO" 2>/dev/null || echo 0; }
# Cerca, DOPO la riga $1, il primo evento di tipo $2 e ne stampa il JSON.
cerca()
{
	python3 - "$VISTO" "$1" "$2" <<'PY'
import json, os, sys
p, minimo, tipo = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if not os.path.exists(p):
    sys.exit(1)
for r in open(p, encoding="utf-8").read().splitlines()[minimo:]:
    try: d = json.loads(r)
    except Exception: continue
    if d.get("tipo") == tipo:
        print(json.dumps(d)); sys.exit(0)
sys.exit(1)
PY
}
attendi() { local i=0 o; while [ $i -lt "${3:-8}" ]; do o=$(cerca "$1" "$2") && { printf '%s\n' "$o"; return 0; }; sleep 1; i=$((i+1)); done; return 1; }
campo()  { python3 -c 'import json,sys
try: print(json.loads(sys.stdin.read()).get(sys.argv[1]))
except Exception: print("")' "$1"; }

# ---------------------------------------------------------------------------
log "3. Il testimone — una finestra VERA, sul monitor $TELA"

# ⛔⛔ IL FILE SI AZZERA UNA VOLTA PER GIRO, NON A OGNI RIAPERTURA — e queste
#     due righe sono costate due giri, in DUE direzioni opposte:
#
#   azzerandolo a ogni riapertura   il testimone si riapre dopo il ricambio di
#                                   geometria, e ⛔ sparisce **tutto quel che ha
#                                   visto prima** — cioe' la prova di meta' del
#                                   banco.  Il primo deposito ne portava 16 su 45;
#   non azzerandolo mai             il controllo di prontezza trovava il `PRONTA`
#                                   del giro PRECEDENTE e diceva «pronto» a un
#                                   testimone che non era ancora nato.  ⛔ Due NO
#                                   su difetti inesistenti, e uno accusava il
#                                   prodotto.
#
# ⇒ Azzerato qui, una volta; e la prontezza si cerca **dopo la riga corrente**.
: > "$VISTO"; chmod 666 "$VISTO"

avvia_testimone() # $1 = misura
{
	local n i=0
	n=$(righe)
	come_prova "$TEST" --misura "${1:-$TELA}" >>"$VISTO" 2>&1 &
	while [ $i -lt 30 ]; do
		cerca "$n" PRONTA >/dev/null 2>&1 && { TESTIMONE_DA=$n; return 0; }
		cerca "$n" ERRORE >/dev/null 2>&1 && { TESTIMONE_DA=$n; return 1; }
		sleep 1; i=$((i + 1))
	done
	TESTIMONE_DA=$n
	return 1
}
if ! avvia_testimone "$TELA"; then
	ko "il testimone non si e' aperto:"
	sed 's/^/        /' "$VISTO" | tail -12
	exit 5
fi
tail -n "+$((TESTIMONE_DA + 1))" "$VISTO" \
    | grep -E '"SCHERMO"|"PRONTA"|"POSTO_LEGATO"|"KEYMAP"' | sed 's/^/        /'
ok "testimone aperto sul monitor giusto"

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
log "4. ⭐ IL PUNTATORE — dove finisce davvero"

prova_puntatore()
{
	local n o x y
	n=$(righe); manda "punta $1 $2"
	o=$(attendi "$n" PUNTATORE 8) || { ko "punta $1,$2 → il testimone non ha visto NULLA"; return; }
	x=$(printf '%s' "$o" | campo x); y=$(printf '%s' "$o" | campo y)
	if [ "${x%.*}" = "$1" ] && [ "${y%.*}" = "$2" ]; then
		ok "punta $1,$2 → la finestra ha visto $x,$y"
	else
		ko "punta $1,$2 → la finestra ha visto $x,$y"
	fi
}
# ⛔ Un movimento di riscaldamento che NON si giudica: il primo spostamento
#    puo' cadere sullo stesso punto dell'`enter`, e Wayland non emette `motion`
#    se la posizione non cambia — «stessa posizione» e «non consegnato» hanno lo
#    stesso aspetto (`CODER.md` §3.10).
manda "punta 5 5"; sleep 2
prova_puntatore 100 100
prova_puntatore $((LARG - 1)) $((ALT - 1))
prova_puntatore $((LARG / 2)) $((ALT / 2))

# ---------------------------------------------------------------------------
log "5. ⛔⛔ LA ROTELLA — il segno, nei DUE versi"

# ⛔ «Qualcosa si muove» non e' una misura del segno: si inietta +120 E -120, e
#    si pretende che i due arrivi abbiano segno OPPOSTO.
# ⚠ Il ponte con `deltaY` della pagina (che e' come `RCP.md` §7.3 l'ha misurato
#   il 10 agosto) e' la convenzione di `wl_pointer.axis`: **positivo nel verso
#   in cui il contenuto si muove**, cioe' `axis` positivo ⇔ `deltaY` positivo
#   ⇔ la pagina SCENDE.  E' `[S]`, e sta scritta qui perche' si veda.
rotella() # $1 = asse_y mandato → stampa "v120 axis"
{
	local n o120 oa
	n=$(righe); manda "rotella 0 $1"
	o120=$(attendi "$n" ASSE_120 6); oa=$(cerca "$n" ASSE)
	printf '%s %s\n' "$(printf '%s' "$o120" | campo v120)" "$(printf '%s' "$oa" | campo valore)"
}
read -r V_SU A_SU   <<< "$(rotella 120)"
read -r V_GIU A_GIU <<< "$(rotella -120)"
inf "il client manda +120 (l'utente gira IN SU)  → axis_value120=$V_SU  axis=$A_SU"
inf "il client manda -120 (l'utente gira IN GIU) → axis_value120=$V_GIU axis=$A_GIU"

python3 - "$V_SU" "$V_GIU" "$A_SU" "$A_GIU" <<'PY'
import sys
def n(x):
    try: return float(x)
    except Exception: return None
vsu, vgiu, asu, agiu = (n(x) for x in sys.argv[1:5])
V, G = "\033[1;32mOK\033[0m", "\033[1;31mNO\033[0m"
if vsu is None or vgiu is None:
    print(f"    {G}  uno dei due versi non e' arrivato: il segno NON e' misurato"); sys.exit(1)
if vsu == 0 or vgiu == 0:
    print(f"    {G}  un valore e' zero: non si misura un segno su uno zero"); sys.exit(1)
if (vsu > 0) == (vgiu > 0):
    print(f"    {G}  i due versi danno lo STESSO segno ({vsu} e {vgiu}): non si sta")
    print( "         misurando il segno, si sta misurando «qualcosa si muove»"); sys.exit(1)
if vsu > 0:
    print(f"    {G}  +120 (utente IN SU) → axis_value120={vsu} > 0, cioe' il contenuto")
    print( "         SCENDE: lo schermo remoto scorre AL CONTRARIO.  Inversione NON in vigore.")
    sys.exit(1)
print(f"    {V}  +120 (utente IN SU)  → axis_value120={vsu} < 0: il contenuto SALE, come deve")
print(f"    {V}  -120 (utente IN GIU) → axis_value120={vgiu} > 0: il contenuto SCENDE")
print(f"    {V}  e i due strumenti concordano: axis liscio {asu} e {agiu}")
PY
[ $? -ne 0 ] && ESITO=1

log "5-bis. ⛔ I MEZZI SCATTI — 60 non si arrotonda a zero"
# `STUDI.md` §gnome §9: `ei_device_scroll_discrete` fa una divisione INTERA per 120 e
# se li mangia.  `src/input.c` va di `scroll_delta`, dove la soglia e' 60.
read -r V_MEZZO A_MEZZO <<< "$(rotella 60)"
if [ -z "$V_MEZZO$A_MEZZO" ] || { [ "$V_MEZZO" = None ] && [ "$A_MEZZO" = None ]; }; then
	ko "mezzo scatto (60) → NIENTE e' arrivato: i mezzi scatti SPARISCONO"
else
	ok "mezzo scatto (60) → axis_value120=$V_MEZZO axis=$A_MEZZO: NON si arrotonda a zero"
fi

# ⛔ E l'orizzontale, nei due versi: il contratto dice che NON si inverte, e
#    «non si inverte» e' un'affermazione da misurare come le altre.
orizz()
{
	local n o
	n=$(righe); manda "rotella $1 0"
	o=$(attendi "$n" ASSE_120 6) && printf '%s %s\n' "$(printf '%s' "$o" | campo asse)" \
	                                                 "$(printf '%s' "$o" | campo v120)"
}
read -r AX_D V_D <<< "$(orizz 120)"
read -r AX_S V_S <<< "$(orizz -120)"
inf "orizzontale: +120 → asse=$AX_D v120=$V_D  ·  -120 → asse=$AX_S v120=$V_S"
if [ "$V_D" = 120 ] && [ "$V_S" = -120 ]; then
	ok "l'orizzontale passa COM'E', nei due versi: giusto non invertirlo"
elif [ -z "$V_D" ] || [ -z "$V_S" ]; then
	ko "l'orizzontale non e' arrivato in uno dei due versi"
else
	ko "l'orizzontale esce come $V_D / $V_S invece di 120 / -120"
fi

# ---------------------------------------------------------------------------
log "6. I PULSANTI e le POSIZIONI"

N=$(righe); manda "pulsante 272 1"; sleep 1; manda "pulsante 272 0"
O=$(attendi "$N" BOTTONE 8)
if [ -n "$O" ]; then
	B=$(printf '%s' "$O" | campo bottone)
	[ "$B" = 272 ] && ok "BTN_LEFT (272) → la finestra ha visto il bottone $B" \
	               || ko "BTN_LEFT (272) → la finestra ha visto il bottone $B"
else
	ko "BTN_LEFT (272) → la finestra non ha visto nessun bottone"
fi

N=$(righe); manda "posizione 30 1"; sleep 1; manda "posizione 30 0"
O=$(attendi "$N" TASTO 8)
if [ -n "$O" ]; then
	C=$(printf '%s' "$O" | campo codice)
	[ "$C" = 30 ] && ok "KEY_A (30) → la finestra ha visto il codice $C" \
	              || ko "KEY_A (30) → la finestra ha visto il codice $C"
else
	ko "KEY_A (30) → la finestra non ha visto nessun tasto"
fi

N=$(righe); manda "lettera 97"      # 'a', valore scalare Unicode
sleep 3
O=$(cerca "$N" TASTO)
if [ -n "$O" ]; then
	ok "LETTERA U+0061 → la finestra ha visto il codice $(printf '%s' "$O" | campo codice)"
	grep -q "RIPIEGO DEL BANCO" "$LAVORO/iniettore.log" && \
	  inf "   ⚠ vale [?] e non [M]: sopra c'e' la riga «RIPIEGO DEL BANCO» (tastiera.c di A5)"
else
	dubbio "LETTERA U+0061 → niente.  Il ritorno di input_lettera: $(grep -o 'B24: lettera 97 -> .*' "$LAVORO/iniettore.log" | tail -1)"
fi

# ---------------------------------------------------------------------------
log "7. ⛔⛔ IL RILASCIO AL DISTACCO — si stacca CON UN TASTO PREMUTO"

# `RCP.md` §11: la regola col rapporto danno/costo piu' alto del documento.
#
# ⛔⛔ E PRIMA SI RIPORTA IL FUOCO NELLA FINESTRA, E SI VERIFICA CHE CI SIA.
#
#    `[M]` 14 agosto 2026, primo giro col testimone: questa prova girava DOPO i
#    due ricambi, e il testimone aveva perso il fuoco (`FUOCO dentro:0`) e poi
#    il posto aveva perso tastiera e puntatore.  ⛔ Il banco stampava «la
#    finestra NON ha visto il rilascio» — vero, e per una ragione che col
#    rilascio non c'entra niente.  Un rosso che ACCUSA LA COSA SBAGLIATA e' il
#    peggiore dei rossi.  ⇒ La prova sta prima dei ricambi, e comincia con un
#    controllo positivo sul fuoco.
# ⛔ E si punta a un posto DIVERSO da dove il puntatore gia' sta: Wayland non
#    emette `motion` se la posizione non cambia, e ⛔ «stessa posizione» e «non
#    consegnato» hanno lo stesso aspetto — `CODER.md` §3.10, e questo controllo
#    ci e' cascato al primo giro (`[M]` 14 ago 2026: stampava NO subito prima di
#    un OK che diceva il contrario).
N=$(righe); manda "punta $((LARG / 3)) $((ALT / 3))"
if ! attendi "$N" PUNTATORE 8 >/dev/null; then
	ko "la finestra non riceve piu' il puntatore: la prova del rilascio non e' valida"
fi
N=$(righe); manda "posizione 30 1"; sleep 1; manda "posizione 30 0"
if attendi "$N" TASTO 8 >/dev/null; then
	ok "controllo positivo: la finestra ha il fuoco e riceve i tasti"
else
	ko "la finestra NON ha il fuoco: quel che segue non misura il rilascio"
fi

manda "posizione 29 1"; sleep 1      # KEY_LEFTCTRL giu', e li' si lascia
manda "pulsante 272 1"; sleep 1      # e il bottone sinistro
manda "stato"; sleep 2
CONTO=$(grep -o 'tasti_premuti=[0-9]* pulsanti_premuti=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
inf "prima del rilascio: $CONTO"
case "$CONTO" in
*"tasti_premuti=1 pulsanti_premuti=1"*) ok "il conto e' tenuto: 1 tasto e 1 pulsante" ;;
*) ko "il conto NON torna: «$CONTO» invece di «tasti_premuti=1 pulsanti_premuti=1»" ;;
esac

N=$(righe)
manda "rilascia"; sleep 3
QUANTI=$(grep -o 'B24: RILASCIATI [0-9-]*' "$LAVORO/iniettore.log" | tail -1 | awk '{print $3}')
if [ "$QUANTI" = 2 ]; then
	ok "input_rilascia_tutto() ne ha rilasciati $QUANTI, ed e' il numero giusto"
else
	ko "input_rilascia_tutto() ne ha rilasciati «$QUANTI» invece di 2"
fi
# ⛔ E DAL LATO CHE RICEVE: la finestra ha visto i due rilasci?
SU_TASTO=$(cerca "$N" TASTO); SU_BOTT=$(cerca "$N" BOTTONE)
if [ -n "$SU_TASTO" ] && [ "$(printf '%s' "$SU_TASTO" | campo premuto)" = 0 ]; then
	ok "la finestra ha visto il RILASCIO del tasto $(printf '%s' "$SU_TASTO" | campo codice)"
else
	ko "la finestra NON ha visto il rilascio del tasto: il conto e' tornato, l'evento no"
fi
if [ -n "$SU_BOTT" ] && [ "$(printf '%s' "$SU_BOTT" | campo premuto)" = 0 ]; then
	ok "la finestra ha visto il RILASCIO del bottone $(printf '%s' "$SU_BOTT" | campo bottone)"
else
	ko "la finestra NON ha visto il rilascio del bottone"
fi
manda "stato"; sleep 2
CONTO=$(grep -o 'tasti_premuti=[0-9]* pulsanti_premuti=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
case "$CONTO" in
*"tasti_premuti=0 pulsanti_premuti=0"*) ok "dopo il rilascio il conto e' a zero" ;;
*) ko "dopo il rilascio resta «$CONTO»" ;;
esac

log "8. ⛔ IL CONTROLLO DEL SILENZIO — dieci secondi senza iniettare"

# ⛔ Non e' «non ho trovato righe»: e' la differenza di un CONTATORE su uno
#    strumento che ha appena dimostrato di saper contare eventi veri.
PRIMA=$(righe)
sleep 10
DOPO=$(righe)
inf "righe del testimone: $PRIMA → $DOPO in dieci secondi di silenzio"
if [ "$PRIMA" = "$DOPO" ]; then
	ok "dieci secondi senza iniettare: ZERO eventi, e lo strumento ne ha gia' visti $DOPO"
else
	ko "in dieci secondi SENZA iniettare sono arrivati $((DOPO - PRIMA)) eventi:"
	tail -n "$((DOPO - PRIMA))" "$VISTO" | head -5 | sed 's/^/        /'
fi

# ---------------------------------------------------------------------------
log "9. ⛔⛔ IL RICAMBIO DELLA KEYMAP — si cambia disposizione IN CORSA"

SORG_PRIMA=$(come_prova gsettings get org.gnome.desktop.input-sources sources 2>/dev/null)
inf "disposizione di partenza: $SORG_PRIMA"
manda "stato"; sleep 2
RT_PRIMA=$(grep -o 'ricambi_tastiera=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
KM_PRIMA=$(grep -c 'KEYMAP CAMBIATA' "$LAVORO/iniettore.log")
N=$(righe)

come_prova gsettings set org.gnome.desktop.input-sources sources "[('xkb','de')]" 2>/dev/null
sleep 6
manda "stato"; sleep 2
RT_DOPO=$(grep -o 'ricambi_tastiera=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
KM_DOPO=$(grep -c 'KEYMAP CAMBIATA' "$LAVORO/iniettore.log")
inf "ricambi della tastiera: $RT_PRIMA → $RT_DOPO   ·   letture di keymap diverse: $KM_PRIMA → $KM_DOPO"
KM_VISTA=$(cerca "$N" KEYMAP)
[ -n "$KM_VISTA" ] && inf "e la finestra ha ricevuto una keymap nuova: $KM_VISTA"

if [ "$RT_PRIMA" = "$RT_DOPO" ] && [ "$KM_PRIMA" = "$KM_DOPO" ]; then
	dubbio "il ricambio della KEYMAP non e' stato riprodotto: il banco resta verde e lo"
	printf '         DICHIARA — non e una prova che il difetto non ci sia (CODER.md §3.4)\n'
else
	ok "il ricambio c'e' stato, e il modulo l'ha VISTO"
	N=$(righe); manda "posizione 30 1"; sleep 1; manda "posizione 30 0"
	O=$(attendi "$N" TASTO 8)
	[ -n "$O" ] && ok "dopo il ricambio i tasti arrivano ancora (codice $(printf '%s' "$O" | campo codice))" \
	            || ko "dopo il ricambio i tasti NON arrivano piu': il difetto e' vivo"
fi
come_prova gsettings set org.gnome.desktop.input-sources sources "$SORG_PRIMA" 2>/dev/null
sleep 3
inf "disposizione rimessa: $(come_prova gsettings get org.gnome.desktop.input-sources sources 2>/dev/null)"

# ---------------------------------------------------------------------------
log "10. ⛔⛔ IL RICAMBIO DELLA GEOMETRIA — cambia SOTTO il dispositivo in uso"

manda "stato"; sleep 2
RP_PRIMA=$(grep -o 'ricambi_puntatore=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
manda "ridimensiona 1280 720"
sleep 8
manda "stato"; sleep 2
RP_DOPO=$(grep -o 'ricambi_puntatore=[0-9]*' "$LAVORO/iniettore.log" | tail -1)
inf "ricambi del puntatore: $RP_PRIMA → $RP_DOPO"
if [ "$RP_PRIMA" = "$RP_DOPO" ]; then
	dubbio "il ricambio della GEOMETRIA non e' stato riprodotto: dichiarato, non concluso"
else
	ok "il ricambio c'e' stato, e il modulo l'ha VISTO: $RP_DOPO"
	# ⛔ E la domanda vera: dopo il ricambio il puntatore si muove ANCORA?
	sudo -A pkill -f 04-b24-testimone 2>/dev/null; sleep 2
	manda "ritela 1280 720"; sleep 1
	if avvia_testimone 1280x720; then
		N=$(righe); manda "punta 640 360"
		O=$(attendi "$N" PUNTATORE 10)
		[ -n "$O" ] && ok "dopo il ricambio il puntatore si muove ancora: $(printf '%s' "$O" | campo x),$(printf '%s' "$O" | campo y)" \
		            || ko "dopo il ricambio il puntatore NON si muove piu': il difetto e' vivo"
	else
		dubbio "il testimone non si e' riaperto a 1280x720: la seconda meta' resta aperta"
	fi
fi

# ---------------------------------------------------------------------------
printf '\n'
printf '⚠ E LA META CHE RESTA APERTA, dichiarata invece che taciuta: alla fase 4 NON\n'
printf '  c e ancora una sessione a cui RIATTACCARSI (PIANO.md, fase 5).  Qui si misura\n'
printf '  il CONTEGGIO e l EVENTO che ne esce — non «al riattacco il Ctrl non era\n'
printf '  rimasto giu».  Quella meta e della fase 5.\n'

# ---------------------------------------------------------------------------
log "Il verdetto"
if [ "$ESITO" = 0 ]; then
	printf '    \033[1;32mB24 VERDE\033[0m — una finestra vera, sul monitor giusto, ha visto\n'
	printf '    arrivare quel che abbiamo iniettato, col segno giusto.\n'
else
	printf '    \033[1;31mB24 ROSSO\033[0m — vedi le righe NO qui sopra.\n'
fi
exit "$ESITO"
