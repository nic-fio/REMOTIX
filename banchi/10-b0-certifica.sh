#!/usr/bin/env bash
# ===========================================================================
# 10-b0-certifica.sh — ⛔⛔ IL CONTROLLO DEL TERRENO, VISTO MORDERE.
#
#   bash banchi/10-b0-terreno.sh --certifica        ← si chiama cosi'
#
# `LEZIONI.md` §1.29: **un banco non e' finito finche' non lo si e' visto dare
# ROSSO**, e per un controllo del terreno vale doppio — se non morde e' **peggio
# che non averlo**, perche' fa credere che qualcuno stia guardando.
#
# ⛔ Qui ogni predicato di `10-b0-terreno.sh` ha il suo guasto, il guasto viene
#    **fatto girare** (non immaginato), e si conta **sano → guasto → risanato**.
#    Il conto a tre passi non e' pignoleria: un guasto che resta rosso anche
#    dopo essere stato tolto vuol dire che il rosso lo dava qualcos'altro.
#
# ⚠ LA SCENA DELLA CERTIFICAZIONE, e va detta perche' non e' un albero vero:
#   si lavora su un albero **finto** — `$LAV/albero-prova` — fatto di una copia
#   dei sorgenti del repo e di un binario `remotix` **copiato** da un albero
#   gia' costruito.  ⛔ Non si compila niente: gli altri nove agenti stanno
#   misurando adesso, e una costruzione sarebbe mezzo minuto di carico su venti
#   filiere.  ⇒ Qui si certifica il CONTROLLO, non un albero.
#
# ⚠ E il lucchetto della GPU **vero** non si tocca nemmeno per prova: i guasti
#   sul lucchetto si innestano su `$LUCCHETTO` di prova, che e' un posto mio.
#   Il `netem` su `lo`, che invece e' uno solo per tutti, si innesta **dopo aver
#   preso il lucchetto del netem**, dura due secondi e si verifica di averlo
#   tolto — non lo si dichiara a memoria.
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")" && pwd)
REPO_VERO=$(cd "$QUI/.." && pwd)
TERRENO=$QUI/10-b0-terreno.sh

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
CHI=${CHI:-10-a7}
PORTA=${PORTA:-7977}
UTENTE=${UTENTE:-prova2}
LAV=${LAV:-/media/REMOTIX/tmp/10a7}
ALBERO=${ALBERO:-$LAV/albero-prova}
LUCPROVA=/media/REMOTIX/tmp/.lucchetto-10a7-prova.d
LUCNETEM=/media/REMOTIX/tmp/.lucchetto-netem.d
BANPROVA=$LAV/ban-prova

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'
GRIGIO=$'\033[0m'; NETTO=$'\033[1m'
tit() { printf '\n%s%s%s\n' "$NETTO" "$*" "$GRIGIO"; }
inf() { printf '    --  %s\n' "$*"; }

SCR=$(mktemp -d) || exit 2
trap 'rm -rf "$SCR"' EXIT

# ⚠ Il profilo della macchina di prova stampa «tput: No value for $TERM» su
#   stderr a ogni ssh: con `2>&1` quella riga finisce DENTRO i dati — e ci era
#   gia' finita, dentro l'elenco delle porte tollerate.
rem()  { timeout 60 ssh -o BatchMode=yes "$MACCHINA" "$1" 2>/dev/null; }
root() { timeout 90 ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' $1" 2>&1 | grep -v '^tput:'; }
# ⛔ L'innestatore e' un FILE gia' sulla macchina, e `sudo -S` riceve solo la
#    parola: dargli il copione sullo stdin vorrebbe dire togliergli la parola.
inn()  { root "env LAV='$LAV' ALBERO='$ALBERO' LUCCHETTO='$LUCPROVA' \
	BAN_FILE='$BANPROVA' bash $LAV/10-b0-innesta.sh $1"; }

printf '\n%s╔═ ⛔⛔ 10-b0-terreno.sh — LO SI VEDE MORDERE%s\n' "$NETTO" "$GRIGIO"

# ── 0 · la scena ──────────────────────────────────────────────────────────
tit "== 0 · la scena della certificazione"
mkdir -p "$SCR/repo/banchi"
cp -a "$REPO_VERO/src" "$SCR/repo/src" || exit 2
cp -a "$REPO_VERO/banchi/rcp" "$SCR/repo/banchi/rcp" || exit 2
inf "repo di prova (una copia, l'originale non si tocca): $SCR/repo"

# ⛔⭐ L'ALBERO DI PROVA SI RIFA' A OGNI GIRO, e la ragione e' proprio quella
#     che questo controllo certifica: un albero di prova lasciato li' invecchia
#     in silenzio, e al primo `src/*.c` toccato nel repo il giro SANO diventa
#     rosso su T5.2 — cioe' la certificazione si fermerebbe accusando il
#     predicato invece della scena.  ⇒ si rispedisce, e non si compila niente.
tar -C "$REPO_VERO" --exclude='src/remotix' --exclude='src/*.o' -czf - src | \
	timeout 120 ssh -o BatchMode=yes "$MACCHINA" \
	"rm -rf $ALBERO && mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
	printf '  ⛔ i sorgenti di prova non sono arrivati in %s\n' "$ALBERO"; exit 2; }

# ⛔ E il binario NON si costruisce: se ne COPIA uno gia' costruito da un albero
#    qualunque della macchina.  ⚠ Quel binario non c'entra con questi sorgenti,
#    e va detto: qui si certifica il CONTROLLO — che guarda md5, date, `ldd` e
#    quanti binari ci sono — non un albero vero.  Costruire vorrebbe dire mezzo
#    minuto di venti filiere tolte agli altri nove agenti.
PRESTATO=$(rem "find /media/REMOTIX/src -maxdepth 3 -type f -name remotix -perm -u+x -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-")
PRESTATO=$(printf '%s' "$PRESTATO" | tr -d '\r')
if [ -z "$PRESTATO" ]; then
	printf '  ⛔ nessun binario «remotix» gia' "'" 'costruito da cui copiare\n'; exit 2
fi
rem "cp -p '$PRESTATO' $ALBERO/src/remotix && touch $ALBERO/src/remotix" >/dev/null
rem "test -x $ALBERO/src/remotix" >/dev/null || {
	printf '  ⛔ il binario prestato non e'"'"' arrivato in %s/src\n' "$ALBERO"; exit 2; }
inf "albero di prova rifatto: $ALBERO  (binario prestato da $PRESTATO)"
timeout 60 ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $LAV && cat > $LAV/10-b0-innesta.sh" <"$QUI/10-b0-innesta.sh" || exit 2
inf "innestatore spedito in $LAV/10-b0-innesta.sh"

# ⛔ LE PORTE DEGLI ALTRI SI DICHIARANO, e si stampano: tacerle sarebbe la
#    forma cattiva — un banco che non si accorge dei vicini da' un numero
#    plausibile, non un rosso.
AMMESSE=$(rem "ss -tuln | grep -oE ':(7|8)[0-9]{3}\b' | tr -d : | sort -u | tr '\n' ' '")
AMMESSE=$(printf '%s' "$AMMESSE" | tr -s ' ')
inf "porte di ALTRI agenti vive adesso, tollerate per dichiarazione: ${AMMESSE:-nessuna}"
inf "⚠ e' la scena reale della fase 10: nove agenti sulla stessa macchina"

BASE=(CHI="$CHI" PORTA="$PORTA" UTENTE="$UTENTE" ALBERO="$ALBERO" LAV="$LAV"
      REPO="$SCR/repo" LUCCHETTO="$LUCPROVA" BAN_FILE="$BANPROVA"
      PORTE_AMMESSE="$AMMESSE" MACCHINA="$MACCHINA" PAROLA_SUDO="$PAROLA_SUDO"
      IND="$IND")

USC=0
giro() # $1 = file esiti · resto = scavalcamenti d'ambiente
{
	local f=$1; shift
	rm -f "$f"
	env "${BASE[@]}" "$@" ESITI_FUORI="$f" bash "$TERRENO" >"$SCR/ultimo.txt" 2>&1
	USC=$?
	N_GIRI=$((N_GIRI + 1))
}
es() { awk -F'\t' -v k="$2" '$1==k {print $2; exit}' "$1" 2>/dev/null; }
tx() { awk -F'\t' -v k="$2" '$1==k {print $3; exit}' "$1" 2>/dev/null; }

N_GIRI=0; ATTESI=0; PASSATI=0; SALTATI=0
SANO=$SCR/sano.txt; GUA=$SCR/guasto.txt

# verdetto <sigla> <nome> <atteso al guasto> [parola che deve comparire]
verdetto()
{
	local s=$1 nome=$2 att=$3 parola=${4:-}
	local a b c
	a=$(es "$SANO" "$s"); b=$(es "$GUA" "$s"); c=$(es "$SCR/risanato.txt" "$s")
	ATTESI=$((ATTESI + 1))
	local bene=si
	[ "$a" = VERDE ]   || bene=no
	[ "$b" = "$att" ]  || bene=no
	[ "$c" = VERDE ]   || bene=no
	if [ -n "$parola" ]; then
		case "$(tx "$GUA" "$s")" in *"$parola"*) ;; *) bene=no ;; esac
	fi
	if [ "$bene" = si ]; then
		PASSATI=$((PASSATI + 1))
		printf '  %s⭐%s %-6s %-46s %s→%s→%s\n' "$VERDE" "$GRIGIO" "$s" "$nome" \
			"${a:-?}" "${b:-?}" "${c:-?}"
	else
		printf '  %s✗ %s %-6s %-46s %s→%s→%s   (atteso VERDE→%s→VERDE%s)\n' \
			"$ROSSO" "$GRIGIO" "$s" "$nome" "${a:-VUOTO}" "${b:-VUOTO}" "${c:-VUOTO}" \
			"$att" "${parola:+, con «$parola»}"
		printf '        motivo al guasto: %s\n' "$(tx "$GUA" "$s")"
	fi
}
salta() { SALTATI=$((SALTATI + 1))
	printf '  %s⚠ %s %-6s %-46s NON INNESTATO: %s\n' "$GIALLO" "$GRIGIO" "$1" "$2" "$3"; }

# ── il giro sano di partenza ──────────────────────────────────────────────
tit "== 1 · il giro SANO di partenza"
giro "$SANO"
V=$(grep -c 'VERDE' "$SANO"); R=$(grep -c 'ROSSO' "$SANO"); I=$(grep -c 'IGNOTO' "$SANO")
inf "uscita $USC · $V verdi, $R rossi, $I ignoti su $(wc -l <"$SANO") predicati"
if [ "$R" -ne 0 ] || [ "$I" -ne 0 ]; then
	printf '  %s⛔ IL GIRO SANO NON E'"'"' VERDE: la certificazione non vale.%s\n' "$ROSSO" "$GRIGIO"
	grep -E 'ROSSO|IGNOTO' "$SANO" | sed 's/^/        /'
	inf "⚠ Un guasto innestato su un terreno gia' rosso non dimostra niente:"
	inf "  non si distingue il rosso del guasto da quello che c'era prima."
	exit 1
fi
printf '  %s⭐%s il giro sano e'"'"' VERDE su tutti e %s i predicati\n' "$VERDE" "$GRIGIO" "$V"

# ═══════════════════════════════════════════════════════════════════════════
# 2 · I GUASTI DI CONFIGURAZIONE — costano zero alla macchina degli altri
#     ⭐ Sono i piu' onesti che ci siano: non cambiano niente sul ferro, e
#        provano che il predicato guarda DAVVERO quel che dice di guardare.
# ═══════════════════════════════════════════════════════════════════════════
tit "== 2 · i guasti di configurazione (nessun ferro toccato)"

conf() # $1 sigla · $2 nome · $3 atteso · $4 parola|'' · resto = ambiente
{
	local s=$1 n=$2 a=$3 p=$4; shift 4
	giro "$GUA" "$@"
	giro "$SCR/risanato.txt"
	verdetto "$s" "$n" "$a" "$p"
	cp "$SCR/risanato.txt" "$SANO"
}

conf T1.1 "carico oltre il tetto"            ROSSO ""        CARICO_MAX=0.0
conf T1.2 "memoria sotto il minimo"          ROSSO ""        MEM_MIN_MB=99999999
conf T2.2 "il giro produce un numero e il lucchetto non e' mio" ROSSO "" LUCCHETTO_MIO=1
conf T3.1 "l'integrata non e' i915"          ROSSO "amdgpu"  PCI_INTEGRATA=0000:03:00.0
conf T3.2 "la discreta NON e' recintata"     ROSSO "render"  PCI_DISCRETA=0000:00:02.0
conf T3.3 "il gruppo del recinto ha membri"  ROSSO ""        GRUPPO_NOGPU=render
conf T3.2 "l'indirizzo PCI non esiste"       IGNOTO ""       PCI_DISCRETA=0000:99:99.9
conf T4.2 "l'interfaccia non esiste"         IGNOTO ""       IFACCIA=nonesistente0
# ⛔⭐ L'UTENTE COL PALCO VIVO SI SCOPRE SULLA MACCHINA, non si indovina.
#     `[M]` 24 agosto 2026: la prima stesura innestava questo guasto su
#     `nicfio`, che di `gnome-shell` non ne ha — la sua sessione locale non e'
#     quella dei banchi.  Il guasto usciva VERDE, e sembrava un difetto del
#     predicato.  ⚠ Un guasto puntato sul bersaglio sbagliato non e' un guasto:
#     e' un verde in piu' che non dimostra niente.
CON_PALCO=$(rem "pgrep -x gnome-shell | head -1 | xargs -r -I{} stat -c %U /proc/{}")
CON_PALCO=$(printf '%s' "$CON_PALCO" | tr -d ' \n')
if [ -n "$CON_PALCO" ]; then
	inf "l'utente col palco vivo, trovato adesso sulla macchina: «$CON_PALCO»"
	conf T7.1 "l'utente ha un palco vivo ($CON_PALCO)" ROSSO "" UTENTE="$CON_PALCO"
else
	salta T7.1 "l'utente ha un palco vivo" "nessun gnome-shell vivo sulla macchina"
fi

# ⛔ Le porte degli altri, NON dichiarate: e' il caso vero della fase 10.
if [ -n "$AMMESSE" ]; then
	giro "$GUA" PORTE_AMMESSE=""
	giro "$SCR/risanato.txt"
	verdetto T1.3 "un «remotix» di un altro agente, non dichiarato" ROSSO ""
	verdetto T1.4 "una porta di un altro agente, non dichiarata"    ROSSO ""
	cp "$SCR/risanato.txt" "$SANO"
else
	salta T1.3 "un «remotix» di un altro agente" "nessun altro agente e' vivo adesso"
	salta T1.4 "una porta di un altro agente"    "nessuna porta 7xxx/8xxx aperta"
fi

# ⛔ L'albero che non c'e': QUATTRO predicati devono diventare IGNOTI, non verdi.
giro "$GUA" ALBERO="$LAV/albero-che-non-esiste"
giro "$SCR/risanato.txt"
for s in T5.2 T5.3 T5.4 T6; do
	verdetto "$s" "l'albero non c'e' ⇒ «non ho potuto verificare»" IGNOTO ""
done
cp "$SCR/risanato.txt" "$SANO"

# ═══════════════════════════════════════════════════════════════════════════
# 3 · I GUASTI INNESTATI SUI FILE — l'albero e il repo di prova sono miei
# ═══════════════════════════════════════════════════════════════════════════
tit "== 3 · i guasti innestati sui file"

# ── T5.1 · le due copie di rcp.c fatte divergere (R12.3) ──────────────────
printf '/* %s */\n' "10a7 CERTIFICA" >>"$SCR/repo/banchi/rcp/rcp.c"
giro "$GUA"
sed -i '$d' "$SCR/repo/banchi/rcp/rcp.c"
giro "$SCR/risanato.txt"
verdetto T5.1 "le due copie di rcp.c divergono" ROSSO "rcp.c"
cp "$SCR/risanato.txt" "$SANO"

# ── T5.2 · il sorgente spedito NON e' quello che leggo ────────────────────
printf '/* %s */\n' "10a7 CERTIFICA" >>"$SCR/repo/src/main.c"
giro "$GUA"
sed -i '$d' "$SCR/repo/src/main.c"
giro "$SCR/risanato.txt"
verdetto T5.2 "un sorgente spedito diverso da quello locale" ROSSO "main.c"
cp "$SCR/risanato.txt" "$SANO"

# ── ⭐ T5.3 · il binario piu' VECCHIO dei sorgenti ────────────────────────
#    E' il caso che ha salvato la fase 1.
inn bin-vecchio >/dev/null
giro "$GUA"
inn bin-nuovo >/dev/null
giro "$SCR/risanato.txt"
verdetto T5.3 "⭐ il binario e' piu' vecchio di un sorgente" ROSSO "main.c"
cp "$SCR/risanato.txt" "$SANO"

# ── T5.4 · due binari nello stesso albero (D5) ────────────────────────────
inn bin-doppio >/dev/null
giro "$GUA"
inn bin-singolo >/dev/null
giro "$SCR/risanato.txt"
verdetto T5.4 "due binari «remotix» nello stesso albero" ROSSO ""
cp "$SCR/risanato.txt" "$SANO"

# ── T6 · un binario che non lega ngtcp2 ───────────────────────────────────
inn bin-falso >/dev/null
giro "$GUA"
inn bin-vero >/dev/null
giro "$SCR/risanato.txt"
verdetto T6 "un binario che non lega ngtcp2 ne' nghttp3" ROSSO ""
cp "$SCR/risanato.txt" "$SANO"

# ── T8 · il ban dell'indirizzo ────────────────────────────────────────────
inn "ban-metti $IND" >/dev/null
giro "$GUA"
inn ban-togli >/dev/null
giro "$SCR/risanato.txt"
verdetto T8 "l'indirizzo e' bannato per dodici ore" ROSSO "BANNATO"
cp "$SCR/risanato.txt" "$SANO"

# ═══════════════════════════════════════════════════════════════════════════
# 4 · I GUASTI INNESTATI SULLA MACCHINA — brevissimi, e si verifica di averli
#     tolti invece di dichiararlo a memoria
# ═══════════════════════════════════════════════════════════════════════════
tit "== 4 · i guasti innestati sulla macchina (secondi, non minuti)"

# ── ⛔⛔ T2.1 · un lucchetto finto intestato a un altro ────────────────────
inn "luc-finto 10-zz-intruso 600" >/dev/null
giro "$GUA"
inn luc-togli >/dev/null
giro "$SCR/risanato.txt"
verdetto T2.1 "⛔⛔ il lucchetto della GPU e' di un altro" ROSSO "10-zz-intruso"
cp "$SCR/risanato.txt" "$SANO"

# ── T2.1-bis · e uno SCADUTO si DICHIARA, non si scassina in silenzio ─────
inn "luc-finto 10-zz-morto -3600" >/dev/null
giro "$GUA"
ATTESI=$((ATTESI + 1))
sc=$(es "$GUA" T2.1); st=$(tx "$GUA" T2.1)
if [ "$sc" = VERDE ] && case "$st" in *10-zz-morto*) true ;; *) false ;; esac \
   && case "$st" in *SCADUTO*) true ;; *) false ;; esac; then
	PASSATI=$((PASSATI + 1))
	printf '  %s⭐%s %-6s %-46s VERDE, e lo DICHIARA\n' "$VERDE" "$GRIGIO" \
		T2.1 "un lucchetto scaduto: si dichiara, non si scassina"
	grep -q 'SCASSINABILE' "$SCR/ultimo.txt" && \
		printf '        e stampa «SCASSINABILE — e non lo faccio io, e non in silenzio»\n'
else
	printf '  %s✗ %s %-6s uno scaduto doveva essere VERDE+SCADUTO, e'"'"' «%s / %s»\n' \
		"$ROSSO" "$GRIGIO" T2.1 "$sc" "$st"
fi
inn luc-togli >/dev/null
giro "$SANO"

# ── ⛔ T4.1 · il `netem` su `lo`, e il lucchetto del netem si prende ──────
tit "-- il netem su «lo»: si prende PRIMA il lucchetto del netem"
PRESO=no
if LUCCHETTO=$LUCNETEM python3 - "$QUI/09-lucchetto.py" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("luc", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
try:
    m.prendi("10-a7-certifica", secondi=180, attesa=90)
    sys.exit(0)
except m.NonMio as e:
    print("   ⚠ %s" % e); sys.exit(1)
PY
then PRESO=si; fi

if [ "$PRESO" = si ]; then
	inn "netem-metti 1" | sed 's/^/    /'
	giro "$GUA"
	inn netem-togli | sed 's/^/    /'
	giro "$SCR/risanato.txt"
	verdetto T4.1 "un netem dimenticato su «lo»" ROSSO "netem"
	cp "$SCR/risanato.txt" "$SANO"
	LUCCHETTO=$LUCNETEM python3 - "$QUI/09-lucchetto.py" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("luc", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
m.molla("10-a7-certifica")
PY
else
	salta T4.1 "un netem dimenticato su «lo»" "il lucchetto del netem e' di un altro"
fi

# ── T1.3 · un processo «remotix» che non e' mio ───────────────────────────
inn "remotix-finto-avvia 40" | sed 's/^/    /'
giro "$GUA"
inn remotix-finto-togli | sed 's/^/    /'
giro "$SCR/risanato.txt"
verdetto T1.3 "un processo «remotix» vivo che non e' mio" ROSSO ""
cp "$SCR/risanato.txt" "$SANO"

# ── ⛔ T3.4 · qualcuno tiene aperta la DISCRETA (il caso di fase 5) ───────
inn "fd-discreta-avvia 40" | sed 's/^/    /'
giro "$GUA"
inn fd-discreta-togli | sed 's/^/    /'
giro "$SCR/risanato.txt"
verdetto T3.4 "⛔ un processo tiene aperta la scheda esclusa" ROSSO "DISCRETA"
cp "$SCR/risanato.txt" "$SANO"

# ── T7.2 · un cliente rimasto vivo sulla mia porta ────────────────────────
inn "cliente-finto-avvia $PORTA 40" | sed 's/^/    /'
giro "$GUA"
inn "cliente-finto-togli $PORTA" | sed 's/^/    /'
giro "$SCR/risanato.txt"
verdetto T7.2 "un cliente rimasto vivo sulla porta del banco" ROSSO ""
cp "$SCR/risanato.txt" "$SANO"

# ═══════════════════════════════════════════════════════════════════════════
# 5 · ⭐⭐ I CASI CHE SMASCHERANO I CONTROLLI SCRITTI MALE
#     `LEZIONI.md` §1.29: «None non e' zero, e non ho letto non e' non e'
#     successo niente».  Meta' dei nove difetti di banco della fase 9 nasce da
#     questa confusione, e un controllo del terreno che ci cade dichiara pulita
#     una macchina con cui non ha nemmeno parlato.
# ═══════════════════════════════════════════════════════════════════════════
tit "== 5 · ⭐⭐ e se non ho potuto guardare?"
mkdir -p "$SCR/finto"
cat >"$SCR/finto/ssh-muto" <<'FS'
#!/bin/sh
# un ssh che NON risponde: esce 255 e non stampa niente, come una macchina giu'
exit 255
FS
cat >"$SCR/finto/ssh-vuoto" <<'FS'
#!/bin/sh
# ⛔ il caso insidioso: uscita 0, nessun errore, ZERO righe.  E' la faccia
#    esatta di «va tutto bene».
cat >/dev/null 2>/dev/null
exit 0
FS
cat >"$SCR/finto/ssh-troncato" <<'FS'
#!/bin/sh
# uscita 0 e qualche riga vera, ma la raccolta si ferma a meta': niente
# sentinella.  E' un ssh caduto in mezzo, e sembra un successo.
cat >/dev/null 2>/dev/null
printf 'ORA\t1787000000\nCARICO\t0.10 0.10 0.10\nCPU\t20\nMEM_MB\t20000\n'
exit 0
FS
chmod 755 "$SCR/finto"/ssh*

prova_muta() # $1 nome · $2 quale finto ssh · $3 parola attesa nell'uscita
{
	ATTESI=$((ATTESI + 1))
	cp "$SCR/finto/$2" "$SCR/finto/ssh"
	PATH="$SCR/finto:$PATH" env "${BASE[@]}" ESITI_FUORI="$SCR/muto.txt" \
		bash "$TERRENO" >"$SCR/muto-uscita.txt" 2>&1
	local u=$?
	N_GIRI=$((N_GIRI + 1))
	if [ "$u" = 2 ] && grep -q "$3" "$SCR/muto-uscita.txt"; then
		PASSATI=$((PASSATI + 1))
		printf '  %s⭐%s %-53s uscita 2, e dice «%s»\n' "$VERDE" "$GRIGIO" "$1" "$3"
	else
		printf '  %s✗ %s %-53s uscita %s (attesa 2, con «%s»)\n' \
			"$ROSSO" "$GRIGIO" "$1" "$u" "$3"
		tail -4 "$SCR/muto-uscita.txt" | sed 's/^/        /'
	fi
}
prova_muta "ssh che non risponde"                ssh-muto     "NON HO POTUTO VERIFICARE"
prova_muta "ssh muto: uscita 0 e ZERO righe"     ssh-vuoto    "TRONCATA"
prova_muta "ssh caduto in mezzo: niente sentinella" ssh-troncato "TRONCATA"

# ═══════════════════════════════════════════════════════════════════════════
# 6 · ⛔ LA MACCHINA SI LASCIA COM'E' STATA TROVATA, E LO SI VERIFICA
# ═══════════════════════════════════════════════════════════════════════════
tit "== 6 · ⛔ che cosa e' rimasto addosso (si CHIEDE, non si ricorda)"
inn verifica | sed 's/^/    /'
inf "lucchetto VERO della GPU (mai toccato): $(LUCCHETTO=/media/REMOTIX/tmp/.lucchetto-gpu.d \
	python3 "$QUI/09-lucchetto.py" stato 2>&1 | tail -1)"

# ═══════════════════════════════════════════════════════════════════════════
tit "== IL CONTO"
printf '    giri del controllo:  %d\n' "$N_GIRI"
printf '    guasti innestati:    %d\n' "$ATTESI"
printf '    %s%d su %d%s col conto sano → guasto → risanato\n' \
	"$([ "$PASSATI" = "$ATTESI" ] && printf '%s' "$VERDE" || printf '%s' "$ROSSO")" \
	"$PASSATI" "$ATTESI" "$GRIGIO"
[ "$SALTATI" -gt 0 ] && printf '    %s%d%s guasti NON innestati, e dichiarati sopra\n' \
	"$GIALLO" "$SALTATI" "$GRIGIO"
if [ "$PASSATI" = "$ATTESI" ] && [ "$ATTESI" -gt 0 ]; then
	printf '\n    %s⭐ il controllo del terreno MORDE su tutti e %d i guasti.%s\n' \
		"$VERDE" "$ATTESI" "$GRIGIO"
	exit 0
fi
printf '\n    %s⛔ %d guasti NON hanno fatto mordere il controllo.%s\n' \
	"$ROSSO" "$((ATTESI - PASSATI))" "$GRIGIO"
exit 1
