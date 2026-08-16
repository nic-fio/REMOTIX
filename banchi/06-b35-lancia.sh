#!/bin/bash
#
# 06-b35-lancia.sh — ⭐ I COMANDI ESATTI della sottofase 6.3, in un posto solo.
#
# ⛔ GIRA SUL SERVER (NIC-OS), DA ROOT.  Il client lo lancia lui dentro il
#    contenitore: da root `enter.sh` non chiede niente.
#
#   sudo bash .../06-b35-lancia.sh terreno      utente + sessione + scena + server
#   sudo bash .../06-b35-lancia.sh dieci        ⭐ dieci ridimensionamenti di fila
#   sudo bash .../06-b35-lancia.sh limiti       ⭐ i limiti di RCP.md §4.5
#   sudo bash .../06-b35-lancia.sh incatenate [ms] [ripetizioni]
#                                               ⛔ due ADATTA_TELA ravvicinate
#   sudo bash .../06-b35-lancia.sh sweep         la finestra rotta, 10..35 ms x3
#   sudo bash .../06-b35-lancia.sh ricambi       ⭐ i ricambi dei dispositivi
#   sudo bash .../06-b35-lancia.sh registro      le righe della tela del giro
#   sudo bash .../06-b35-lancia.sh tempi         ⭐ le latenze, dal registro
#   sudo bash .../06-b35-lancia.sh pulisci
#
# ⚠ Ogni misura di tempo stampa il CARICO accanto: cinque banchi girano sulla
#   stessa macchina e cinque codificatori sullo stesso iGPU **spostano i
#   millisecondi**.  ⛔ Un numero preso sotto carico e non dichiarato tale e' un
#   numero falso.
#
# ⛔ E LA PAROLA D'ORDINE non passa mai dalla riga di comando (difetto D12):
#    file `0600` scritto con `printf`, `--parola-file`, e una `trap` che lo
#    cancella — anche se il giro si interrompe a meta'.
set -uo pipefail

SANO=${SANO:-/media/REMOTIX/src/06-p-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-p}
PORTA=${PORTA:-7731}
UTENTE=${UTENTE:-provap6}
PAROLA=${PAROLA:-provap6-2026}
C_SANO=${C_SANO:-/srv/src/06-p-src}
C_LAV=${C_LAV:-/srv/remotix/tmp/06-p}
# ⛔⭐ NIENTE APOSTROFI QUI DENTRO — difetto del banco trovato misurando, 16
#     agosto 2026.  La scena si passa al client dentro `--scena '...'`, e un
#     apostrofo ci chiude gli apici: il comando diventa sintatticamente rotto e
#     `enter.sh` esce **senza eseguire niente**, in 350 ms.
#     ⛔ Il giro `ricambi` ha allora contato **ZERO ricambi** — un numero
#     plausibile e falso, su un registro in cui nessuno aveva scritto niente.
#     ⭐ L'ha smascherato il controllo positivo sullo STRUMENTO (`LEZIONI.md`
#     §1.9 regola 2): anche le righe che DEVONO esserci contavano zero.
SCENA=${SCENA:-"gnome-terminal che scrive lora ogni 50 ms, GNOME headless senza --virtual-monitor"}
T="$SANO/banchi/06-b35-terreno.sh"

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { printf '⛔ va lanciato DA ROOT\n'; exit 2; }

P="$LAV/parola"
trap 'rm -f "$P"' EXIT
parola() {
	( umask 077; printf '%s\n' "$PAROLA" > "$P" )
	chmod 600 "$P"
	# ⛔ Il proprietario e' l'utente del CONTENITORE (uid 1000): il client gira
	#    li' dentro, e un file 0600 di root sarebbe illeggibile.
	chown 1000:1000 "$P"
}

# ⭐ I ricambi del PUNTATORE dalla marca in poi.  ⛔ E si conta anche il
#    denominatore — i risvegli del flusso — perche' «4 ricambi» senza «4
#    risvegli» accanto non dice che i due sono la stessa cosa.
ricambi_dalla_marca() {
	local m n r
	m=$(cat "$LAV/registro.marca" 2>/dev/null || echo 0)
	tail -c "+$((m + 1))" "$LAV/registro.log" 2>/dev/null > "$LAV/giro.log"
	n=$(grep -ac "puntatore e.* stato TOLTO" "$LAV/giro.log"); [ -n "$n" ] || n=0
	r=$(grep -ac "flusso RIAVVIATO" "$LAV/giro.log"); [ -n "$r" ] || r=0
	printf '%s (risvegli del flusso: %s)' "$n" "$r"
}

# $1 = giro · $2 = etichetta · resto = argomenti in piu'
cliente() {
	local g=$1 e=$2; shift 2
	parola
	case "$SCENA" in
	*\'*) printf '⛔ SCENA contiene un apostrofo: il comando si romperebbe in\n'
	      printf '   silenzio e il banco conterebbe zero su un registro vuoto.\n'
	      return 9 ;;
	esac
	bash /media/REMOTIX/enter.sh \
		"python3 $C_SANO/banchi/06-b35-tela.py --porta $PORTA \
		 --utente $UTENTE --parola-file $C_LAV/parola --lavoro $C_LAV \
		 --giro $g --etichetta $e --scena '$SCENA' $*"
	local u=$?
	# ⛔ E si guarda l'uscita: 0/4/5 sono misure, tutto il resto e' «il client
	#    non e' partito» — e uno zero contato dopo un client che non e' partito
	#    e' un numero falso.
	case $u in
	0|4|5) : ;;
	*) printf '    ⛔ il client e uscito con %s: NON e una misura\n' "$u" ;;
	esac
	return $u
}

case "${1:-stato}" in
terreno)
	bash "$T" utente   || exit $?
	bash "$T" sessione || exit $?
	bash "$T" scena    || exit $?
	bash "$T" spegni > /dev/null 2>&1
	bash "$T" accendi  || exit $?
	# ⛔ E si verifica che il figlio PARLI, per prima cosa: senza
	#    `--parlantina` i rami tacciono in silenzio, e un'assenza non dimostra
	#    niente.  ⚠ La riga compare solo dopo il primo attacco.
	inf "⚠ «parlantina-c-e» va chiesto DOPO il primo giro: prima il registro e' vuoto"
	exit 0 ;;

dieci|limiti)
	log "Giro «$1» — l'atteso lo dichiara il client, PRIMA"
	bash "$T" carico
	bash "$T" registro-da
	cliente "$1" "$1" --coda 4
	bash "$T" carico
	bash "$T" parlantina-c-e
	exit 0 ;;

incatenate)
	MS=${2:-30}; N=${3:-10}
	log "Giro «incatenate» — due ADATTA_TELA a $MS ms, $N ripetizioni"
	inf "⚠ La tela di PARTENZA si fissa (--base): il palco sopravvive al client"
	inf "  (I4) e senza, ogni giro partirebbe dove l'ha lasciato il precedente."
	bash "$T" carico
	bash "$T" registro-da
	for r in $(seq 1 "$N"); do
		cliente incatenate "c${MS}r${r}" --base 1280x800 \
			--intervallo "$MS" --coda 6 > "$LAV/inc-$MS-$r.txt" 2>&1
		printf '.'
	done
	printf '\n'
	bash "$0" tempi
	exit 0 ;;

sweep)
	log "La FINESTRA ROTTA: intervalli 10..35 ms, 3 giri ciascuno"
	bash "$T" carico
	bash "$T" registro-da
	for r in 1 2 3; do for ms in 10 15 20 25 30 35; do
		cliente incatenate "c${ms}r${r}" --base 1280x800 \
			--intervallo "$ms" --coda 6 > "$LAV/sweep-$ms-$r.txt" 2>&1
		printf '.'
	done; done
	printf '\n'
	python3 - "$LAV" <<-'PY'
	import json, sys, os
	lav = sys.argv[1]
	rotti = tot = 0
	for ms in (10, 15, 20, 25, 30, 35):
	    for r in (1, 2, 3):
	        p = os.path.join(lav, f"06-b35-c{ms}r{r}.json")
	        if not os.path.exists(p):
	            print(f"{ms:3d} ms r{r}: NESSUN JSON"); continue
	        d = json.load(open(p))
	        tele = [v for v in d["controllo_dopo_sessione"] if v["tipo"] == "TELA"]
	        due = tele[1:3]     # il primo risponde alla tela di PARTENZA
	        fin = (due[-1]["tela_l"], due[-1]["tela_a"]) if due else None
	        # ⭐ Il verdetto e' UNO: la tela in vigore alla fine e' quella della
	        #   SECONDA richiesta?  Chi trascina un bordo si aspetta l'ultima.
	        buono = fin == (1024, 640)
	        tot += 1
	        rotti += 0 if buono else 1
	        print(f"{ms:3d} ms r{r}: {'ok   ' if buono else 'ROTTO'} "
	              f"tela finale {fin} · "
	              f"{[ (v['esito'], v['motivo']) for v in due ]} · "
	              f"fuori misura {len(d['fotogrammi_fuori_misura'])}")
	print(f"\nROTTI {rotti} su {tot}")
	PY
	bash "$T" carico
	exit 0 ;;

ricambi)
	# ⭐⭐ IL PUNTO `[?]` DELLA SOTTOFASE 6.1: il ricambio dei dispositivi
	#     avviene SOLO al cambio di tela, o anche al riattacco senza cambio?
	#     ⛔ Da questo dipende se una sola `input_rilascia_tutto()` prima di
	#     `cattura_ridimensiona()` copre tutta la finestra in cui il difetto
	#     morde, o solo meta'.  ⚠ Si MISURA, non si deduce.
	log "I RICAMBI dei dispositivi — due scene, contate a parte"
	bash "$T" carico

	log "scena A: NOVE cambi di tela (giro «dieci»)"
	bash "$T" registro-da > /dev/null
	cliente dieci ric-A --coda 3 > "$LAV/ric-A.txt" 2>&1
	# ⛔ SI CONTA DALLA MARCA, non su tutto il file — difetto del banco trovato
	#    misurando: `registro-coda` legge la coda del registro INTERO, e la
	#    scena B si e' portata dentro i 18 ricambi della scena A.  ⚠ Il numero
	#    era plausibile (22) e falso: quelli di B sono **4**.
	A=$(ricambi_dalla_marca); inf "ricambi in A: $A"

	log "scena B: due attacchi consecutivi alla STESSA tela, ZERO ADATTA_TELA"
	bash "$T" registro-da > /dev/null
	cliente guarda ric-B1 --coda 8 --ping-ogni 3 > "$LAV/ric-B1.txt" 2>&1
	cliente guarda ric-B2 --coda 8 --ping-ogni 3 > "$LAV/ric-B2.txt" 2>&1
	B=$(ricambi_dalla_marca); inf "ricambi in B: $B"

	printf '\n    ⭐ RICAMBI · nove cambi di tela: %s · due riattacchi senza cambio: %s\n' "$A" "$B"
	inf "⚠ Se B > 0 la finestra in cui il difetto morde e' DOPPIA, e una sola"
	inf "  chiamata prima di cattura_ridimensiona() non la copre tutta."
	bash "$T" carico
	exit 0 ;;

tempi)
	# ⭐⭐ LE TRE LATENZE, e sono TRE cose diverse.  ⛔ Metterle sotto una
	#     etichetta sola e' la forma E2: due misure diverse con lo stesso nome.
	log "Le latenze, dal registro del giro (dalla marca in poi)"
	bash "$T" carico
	M=$(cat "$LAV/registro.marca" 2>/dev/null || echo 0)
	tail -c "+$((M + 1))" "$LAV/registro.log" > "$LAV/giro.log" 2>/dev/null
	python3 - "$LAV/giro.log" <<-'PY'
	import re, sys, statistics
	L = [l.rstrip() for l in open(sys.argv[1], errors="replace")]
	def ms(t):
	    h, m, s = t.split(":")
	    return (int(h) * 3600 + int(m) * 60 + float(s)) * 1000
	def quando(sub):
	    return [(ms(l.split()[0]), l) for l in L if sub in l]
	girata = quando("GIRATA al palco")
	chiesta = quando("tela CHIESTA al produttore")
	nuova = quando("TELA NUOVA DAL PALCO")
	spedita = quando("TELA spedita")
	def accoppia(a, b):
	    """Per ogni riga di `a`, la PRIMA di `b` che viene dopo.

	    ⛔ E non si accoppia per indice: se una delle due liste ha un elemento
	       in piu' — e ne ha, ogni volta che il palco si muove da se' — gli
	       indici slittano e si misura la distanza fra eventi di due giri
	       diversi.  ⚠ Un numero plausibile e falso.
	    """
	    fuori, j = [], 0
	    for t, _ in a:
	        while j < len(b) and b[j][0] < t:
	            j += 1
	        if j < len(b):
	            fuori.append(b[j][0] - t)
	    return fuori
	def dillo(nome, v, regola):
	    if not v:
	        print(f"    {nome}: NESSUN CAMPIONE ⛔ (e «nessuno» non e' «zero»)")
	        return
	    print(f"    {nome}: n={len(v)} mediana={statistics.median(v):.1f} ms "
	          f"min={min(v):.1f} max={max(v):.1f}   [{regola}]")
	print()
	dillo("ADATTA_TELA girata → richiesta al produttore",
	      accoppia(girata, chiesta), "rcp.c → figlio.c → cattura.c")
	dillo("richiesta al produttore → fotogramma alla misura nuova",
	      accoppia(chiesta, nuova), "il COMPOSITORE: [M] 41,6 ms su Mutter, 14 ago")
	dillo("⭐ risposta del palco → TELA spedita al client",
	      accoppia(nuova, spedita), "e' il «6 ms» del 15 agosto 2026")
	dillo("ADATTA_TELA girata → TELA spedita (tutto il server)",
	      accoppia(girata, spedita), "il giro intero, lato server")
	PY
	exit 0 ;;

registro)
	bash "$T" registro-tela
	exit 0 ;;

pulisci)
	bash "$T" pulisci
	exit 0 ;;

*)
	bash "$T" stato
	exit 0 ;;
esac
