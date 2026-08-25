#!/bin/bash
#
# 01-s5-tela.sh — S5: la tela che il client dichiara, a zoom 100 % e 150 %.
#                 `SPECIFICHE.md` §6.1-bis · `DECISIONI.md` §5.0-quater
#
#   bash banchi/01-s5-tela.sh              i due motori sullo schermo finto
#   SCHERMO=:0 bash banchi/01-s5-tela.sh   sullo schermo VERO (apre finestre)
#
# ⚠ GIRA DA QUESTA PARTE DEL FILO: i browser stanno sul portatile.
#
# ---------------------------------------------------------------------------
# ⛔ CHE META' DI S5 QUESTO BANCO MISURA, E CHE META' NO
#
# S5 chiede due cose, e sono su due dispositivi:
#
#   ✅ **il browser di questa macchina**, a 100 % e a 150 % — questo banco;
#   ⛔ **che cosa risponde `screen` su DeX** — ⛔ NON MISURATA, e non e' una
#      dimenticanza: vuole il telefono e il DeX, che stanotte non ci sono.
#      «Il Chrome del portatile lo fa» non dice niente del Chrome del
#      telefono: e' la forma d'errore **E10** (`DECISIONI.md` §5-bis.0-ter).
#      Il banco e' lo stesso, la pagina e' la stessa: il giorno che il
#      dispositivo c'e', si apre quell'indirizzo e si legge la riga.
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTROLLO, E PERCHE' QUELLO DI PRIMA ERA ROSSO SU CODICE GIUSTO
#
# Il controllo scritto nella prima stesura diceva *«i due numeri devono
# differire»*.  Ma la tela giusta e' lo schermo in **pixel fisici**, che con lo
# zoom **non cambia**: `screen.width` cala di un terzo, `devicePixelRatio` sale
# di un mezzo, il prodotto resta.  Una pagina scritta bene dava 1920 e 1920 ⇒
# rosso, e chi lo leggeva sarebbe andato a rompere la pagina finche' il numero
# non si muoveva — cioe' a **scrivere** il difetto che §5.0-quater voleva
# evitare (rilievo R3.10).
#
# Qui il controllo e':
#   1. la tela a 100 % e a 150 % e' **la stessa**;
#   2. e coincide con la risoluzione letta **fuori dal browser** (`xdpyinfo`),
#      che e' un secondo strumento sullo stesso fatto;
#   3. ⛔ e lo zoom **e' entrato in vigore davvero** — lo dice
#      `devicePixelRatio`, non il tasto premuto.  Senza questo, «i due numeri
#      sono uguali» sarebbe vero anche non avendo cambiato niente: e' la forma
#      di verde piu' vuota che ci sia, ed e' `KWIN_COMPOSE=O2` un livello piu'
#      in su (`LEZIONI.md` §1.11).
#
# ---------------------------------------------------------------------------
# ⚠ LA SCENA, DICHIARATA
#
# Lo schermo predefinito e' un **Xvfb 1920×1080×24**, cioe' una risoluzione
# che sappiamo perche' l'abbiamo chiesta noi — ed e' un bene per il punto 2:
# la verita' esterna e' nota.  ⛔ Ma va scritta accanto al numero: la tela
# misurata e' quella di QUESTO schermo, non del pannello del portatile.  Con
# `SCHERMO=:0` si misura quello vero, e si aprono finestre sulla scrivania.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-8866}
SCHERMO=${SCHERMO:-:78}
TELA=${TELA:-1920x1080}
REGISTRO=$QUI/01-s5-esiti.jsonl
T=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
PID_X=
PID_RACC=
PID_BR=

congedo()
{
	[ -n "$PID_BR" ]   && { kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; }
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	[ -n "$PID_X" ]    && { kill "$PID_X" 2>/dev/null; wait "$PID_X" 2>/dev/null; }
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "1. Lo schermo, e la verita' fuori dal browser"

if [ "$SCHERMO" = ":0" ]; then
	inf "⚠ schermo VERO: si apriranno finestre sulla scrivania"
else
	Xvfb "$SCHERMO" -screen 0 "${TELA}x24" >"$T/xvfb.log" 2>&1 &
	PID_X=$!
	sleep 2
	if [ ! -d "/proc/$PID_X" ]; then
		ko "Xvfb non e' partito:"
		sed 's/^/        /' "$T/xvfb.log"
		exit 2
	fi
	inf "schermo finto $SCHERMO, chiesto ${TELA}x24"
fi

# ⛔ La risoluzione si LEGGE, non si presume uguale a quella chiesta.
env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdpyinfo >"$T/xdpyinfo.txt" 2>&1
FUORI=$(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$T/xdpyinfo.txt" | head -1)
if [ -z "$FUORI" ]; then
	ko "xdpyinfo non ha dato una risoluzione: senza la verita' esterna il"
	ko "   controllo 2 non esiste, e resterebbe solo «i due numeri sono uguali»"
	sed -n '1,6p' "$T/xdpyinfo.txt" | sed 's/^/        /'
	exit 2
fi
ok "risoluzione letta FUORI dal browser: $FUORI  (xdpyinfo su $SCHERMO)"

# ---------------------------------------------------------------------------
log "2. Il raccoglitore"
python3 -u "$QUI/01-s5-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$T/racc.log"
	exit 3
fi
ok "raccoglitore su 127.0.0.1:$PORTA"

# ---------------------------------------------------------------------------
# Lettura del registro: riga per numero di riga + marchio del giro.
# ⛔ Non «l'ultima riga»: e' il rilievo R8.10 di B2, e S7 l'ha ripagato la
#    stessa sera.
leggi_riga() # $1 = riga minima esclusiva, $2 = giro
{
	python3 - "$REGISTRO" "$1" "$2" <<'PY'
import json, os, sys
percorso, minimo, giro = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if not os.path.exists(percorso):
    sys.exit(1)
righe = open(percorso, encoding="utf-8").read().splitlines()
for i in range(minimo, len(righe)):
    try:
        d = json.loads(righe[i])
    except Exception:
        continue
    if d.get("giro") != giro or d.get("tipo") != "TELA":
        continue
    print(i + 1, d.get("dpr"), f'{d.get("tela_l")}x{d.get("tela_a")}',
          f'{d.get("schermo_l")}x{d.get("schermo_a")}',
          f'{d.get("tela_grezza_l")}x{d.get("tela_grezza_a")}',
          (d.get("motore") or "")[:110], sep="\t")
    sys.exit(0)
sys.exit(1)
PY
}

attendi_riga() # $1 = riga minima, $2 = giro, $3 = secondi
{
	local i=0 t=""
	while [ "$i" -lt "${3:-25}" ]; do
		t=$(leggi_riga "$1" "$2") && { printf '%s\n' "$t"; return 0; }
		sleep 1
		i=$((i + 1))
	done
	return 1
}

ESITI=$T/esiti.tsv
: >"$ESITI"

# ---------------------------------------------------------------------------
# prova_motore <nome> <binario> <opzioni-profilo...>
# ---------------------------------------------------------------------------
prova_motore()
{
	local nome=$1 binario=$2; shift 2
	log "3. $nome"
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	local giro="s5-$nome-$(date +%s)"
	local url="http://127.0.0.1:$PORTA/01-s5-pagina.html?giro=$giro"
	local n riga dpr tela schermo grezza motore

	# ⛔ `[ -f ]` prima: `wc -l < file` su un file che non c'e' fa stampare
	#    l'errore alla SHELL, non a `wc`, e nessun `2>/dev/null` sul comando lo
	#    zittisce.  Un banco che sputa un errore innocuo insegna a chi legge a
	#    non guardare gli errori.
	n=0; [ -f "$REGISTRO" ] && n=$(wc -l < "$REGISTRO")
	mkdir -p "$T/$nome"
	env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@" "$url" >"$T/$nome.log" 2>&1 &
	PID_BR=$!

	riga=$(attendi_riga "$n" "$giro" 45)
	if [ -z "$riga" ]; then
		ko "$nome non ha registrato niente"
		# ⛔ Il denominatore: ha almeno chiesto la pagina?
		inf "richieste al raccoglitore: $(grep -c '^richiesta: ' "$T/racc.log")"
		tail -5 "$T/$nome.log" | sed 's/^/        /'
		ESITO=1
		kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
		return 1
	fi
	IFS=$'\t' read -r n dpr tela schermo grezza motore <<< "$riga"
	ok "a zoom 100 %: dpr=$dpr  schermo=$schermo  tela=$tela  (grezza $grezza)"
	inf "motore: $motore"
	printf '%s\t100\t%s\t%s\t%s\n' "$nome" "$dpr" "$tela" "$schermo" >>"$ESITI"

	# ⛔ LO ZOOM SI PORTA A 150 % E SI VERIFICA CHE CI SIA ARRIVATO.
	#    I passi non sono gli stessi su tutti i motori (Chrome 110-125-150,
	#    Firefox 110-120-133-150): quindi non si contano i tasti, si guarda il
	#    `devicePixelRatio` che la pagina ridichiara a ogni `resize`.
	local i=0 arrivato=no
	while [ "$i" -lt 6 ]; do
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool search --onlyvisible --pid "$PID_BR" \
		    windowactivate --sync windowfocus --sync >/dev/null 2>&1
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdotool key --clearmodifiers ctrl+plus >/dev/null 2>&1
		sleep 2
		riga=$(attendi_riga "$n" "$giro" 6) || { i=$((i + 1)); continue; }
		IFS=$'\t' read -r n dpr tela schermo grezza motore <<< "$riga"
		inf "dopo $((i + 1)) passi di zoom: dpr=$dpr  schermo=$schermo  tela=$tela"
		# Il confronto e' fra numeri con la virgola: si fa in python, non in shell.
		if python3 -c 'import sys; sys.exit(0 if abs(float(sys.argv[1]) - 1.5) < 0.001 else 1)' "$dpr"; then
			arrivato=si
			break
		fi
		i=$((i + 1))
	done

	if [ "$arrivato" = si ]; then
		ok "a zoom 150 %: dpr=$dpr  schermo=$schermo  tela=$tela  (grezza $grezza)"
		printf '%s\t150\t%s\t%s\t%s\n' "$nome" "$dpr" "$tela" "$schermo" >>"$ESITI"
	else
		ko "$nome: non sono riuscito a portare lo zoom a 150 % (ultimo dpr=$dpr)."
		ko "   ⛔ Senza, «i due numeri sono uguali» sarebbe vero anche non avendo"
		ko "   cambiato niente: non e' un esito, e non si registra come tale."
		printf '%s\t150\tNIENTE\tNIENTE\tNIENTE\n' "$nome" >>"$ESITI"
		ESITO=1
	fi

	kill "$PID_BR" 2>/dev/null; wait "$PID_BR" 2>/dev/null; PID_BR=
	sleep 2
	return 0
}

prova_motore chrome google-chrome google-chrome --ozone-platform=x11 \
	--user-data-dir="$T/chrome" --no-first-run --no-default-browser-check --disable-sync
prova_motore firefox firefox firefox --no-remote --profile "$T/firefox"

# ---------------------------------------------------------------------------
log "4. Il verdetto — lo calcola il banco (B0.4)"
python3 - "$ESITI" "$FUORI" <<'PY'
import sys

fuori = sys.argv[2]
righe = [r.rstrip("\n").split("\t") for r in open(sys.argv[1], encoding="utf-8")]
per_motore = {}
for r in righe:
    if len(r) == 5:
        per_motore.setdefault(r[0], {})[r[1]] = r[2:]

guasti = 0
provati = 0
for motore, dati in per_motore.items():
    print(f"\n    {motore}:")
    for zoom in ("100", "150"):
        d = dati.get(zoom, ["-", "-", "-"])
        print(f"      zoom {zoom} %:  dpr={d[0]:>6}  tela={d[1]:>12}  schermo={d[2]:>12}")
    a, b = dati.get("100"), dati.get("150")
    if not a or not b or b[1] == "NIENTE":
        print("      \033[1;31mNO\033[0m  manca una delle due letture: nessun verdetto per questo motore")
        guasti += 1
        continue
    provati += 1
    if a[1] == b[1]:
        print(f"      \033[1;32mOK\033[0m  la tela dichiarata NON cambia con lo zoom: {a[1]}")
    else:
        print(f"      \033[1;31mNO\033[0m  la tela cambia con lo zoom: {a[1]} contro {b[1]}"
              " — ⛔ e' il difetto che DECISIONI.md §5.0-quater teme")
        guasti += 1
    if a[1] == fuori:
        print(f"      \033[1;32mOK\033[0m  e coincide con la risoluzione letta fuori dal browser ({fuori})")
    else:
        print(f"      \033[1;31mNO\033[0m  NON coincide con la risoluzione fuori dal browser: "
              f"{a[1]} contro {fuori}")
        guasti += 1
    # I7: la tela dichiarata deve essere pari sui due assi.
    try:
        l, h = (int(x) for x in a[1].split("x"))
        if l % 2 == 0 and h % 2 == 0:
            print("      \033[1;32mOK\033[0m  la tela dichiarata e' pari sui due assi (invariante I7)")
        else:
            print("      \033[1;31mNO\033[0m  la tela dichiarata ha un lato DISPARI: I7 violata dal client")
            guasti += 1
    except ValueError:
        pass

print()
if provati == 0:
    print("    \033[1;31mNO\033[0m  ⛔ NESSUN motore misurato: non e' un esito, e' un banco che non ha")
    print("           misurato niente.")
    sys.exit(1)
print(f"    -- motori effettivamente misurati: {provati}")
sys.exit(1 if guasti else 0)
PY
[ $? -ne 0 ] && ESITO=1

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "S5, meta' sul browser del portatile: misurata"
else
	ko "S5: qualcosa non torna — vedi sopra"
fi
inf "⛔ E resta NON MISURATA la meta' su DeX: manca il dispositivo."
inf "il dettaglio riga per riga sta in $REGISTRO"
exit "$ESITO"
