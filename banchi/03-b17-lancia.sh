#!/bin/bash
#
# 03-b17-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco dello STEP 5 della fase 3:
# l'anello del ritardo.
#
#   bash banchi/03-b17-lancia.sh certifica   ⭐ gira QUI, senza rete e senza server
#   bash banchi/03-b17-lancia.sh porte       conta 7448 · 7501 · 7561 · 760x · 761x
#   bash banchi/03-b17-lancia.sh porta       copia src/ e i banchi sulla macchina
#   bash banchi/03-b17-lancia.sh costruisci  `make` dentro il contenitore
#   bash banchi/03-b17-lancia.sh terreno     la parola di prova, 0600 (QUI, su CHUWI)
#   bash banchi/03-b17-lancia.sh accendi     prodotto (7615) + ponte (7605+7616)
#   bash banchi/03-b17-lancia.sh scena-costruisci
#   bash banchi/03-b17-lancia.sh misura [secondi]
#   bash banchi/03-b17-lancia.sh stato | registro | spegni | esiti
#   bash banchi/03-b17-lancia.sh tutto
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, E CIASCUNA E' STATA PAGATA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`** — pagata SEI
#     volte: la richiesta della parola di `sudo` va sullo stderr, e una
#     redirezione la mangia.  ⇒ Si passa da `fondamenta/strumenti/sshpw.py`;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare sul
#     server sta in uno SCRIPT (`03-b17-accendi.sh`), non dentro
#     `ssh → enter.sh → bash -c`;
#   · la porta che il browser apre e' la **7605**; dietro c'e' il prodotto sulla
#     **7615** e l'ancora dell'orologio sulla **7616**.  ⛔ La 7448, la 7501, la
#     **7561** (dove l'utente sta guardando il proprio desktop) e la 7603 (dello
#     step 3) si CONTANO prima e dopo, e non si toccano;
#   · l'albero dei sorgenti e' **03-b17-src**, una COPIA;
#   · la parola d'ordine non passa mai da `argv` (difetto D12);
#   · ⛔ **niente `set -e`**: si contano i rossi e si va avanti.
#
# ⛔⭐ E LA DIFFERENZA CON GLI ALTRI STEP: **il browser sta QUI, su CHUWI**.
#     Il prodotto e la scena stanno di la'.  ⇒ Il ritardo attraversa due
#     macchine, e il banco ha un'ANCORA D'OROLOGIO (la 7616) che le lega.
#     ⛔ Senza quell'ancora non si puo' scrivere nessun numero: due orologi
#     monotoni di due macchine non hanno nessuna relazione.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"
FUORI=/media/REMOTIX/src
ALBERO=$FUORI/03-b17-src
DENTRO=/srv/src
PORTA=7605
PORTA_DENTRO=7615
ANCORA=7616
IND=${IND:-192.168.0.2}
LAV=/media/REMOTIX/tmp/03-b17
UTENTE=${UTENTE:-nicfio}
PAROLA_QUI=${PAROLA_QUI:-/tmp/03-b17/parola}
LAVORO_QUI=${LAVORO_QUI:-/tmp/03-b17}
SCHERMO=${SCHERMO:-:85}
DIAGNOSI=${DIAGNOSI:-9605}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

AZIONE=${1:-}

case "$AZIONE" in
certifica)
	# ⛔ Gira QUI, senza rete e senza server: i controlli sono funzioni PURE sul
	#    verbale, cosi' chi revisiona il banco lo puo' riprovare senza toccare
	#    la macchina.  ⭐ E il PONTE si certifica da solo, su loopback.
	python3 "$QUI/03-b17-ritardo.py" --certifica
	exit $? ;;

porte)
	log "Le porte, contate — 7448 · 7501 · 7561 · 7603 NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|760[0-9]|761[0-9])\b' | sort"
	exit 0 ;;

porta)
	log "1. I sorgenti del prodotto, in un albero MIO (una COPIA)"
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO/src $ALBERO/banchi/rcp && mkdir -p $LAV" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	tar czf /tmp/03-b17-src.tgz -C "$RADICE" src banchi/rcp || { ko "tar fallito"; exit 2; }
	metti /tmp/03-b17-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/figlio.c src/pagina.html" \
		|| { ko "l'albero non si e' srotolato"; exit 2; }
	log "2. E i banchi, accanto agli altri"
	# ⛔ `03-scena.c` e' dello STEP 2 e NON si tocca: si porta e si compila in
	#    una cartella mia.  Si dipende, non si riscrive (`CODER.md` §4.1).
	# ⛔⛔ `03-solo.py` VA DI LA', ED E' UN REQUISITO DELLA MISURA, non un di
	#     piu': l'anello attraversa NIC-OS **e** CHUWI, e l'arbitro della
	#     finestra esclusiva guarda **una macchina sola** (`03-solo.py`, limite
	#     n. 1).  ⇒ Senza la copia sul server il banco non puo' sapere se di la'
	#     e' libero, e — per come e' scritto — **si rifiuta di misurare** invece
	#     di dichiararsi solo su meta' anello.
	#     ⚠ Si porta e non si riscrive: un secondo «sono solo?» scritto a mano
	#     farebbe volere alla parola «solo» due cose diverse ai due capi.
	for f in 03-b17-accendi.sh 03-b17-ponte.py 03-scena.c 03-solo.py; do
		metti "$QUI/$f" "$FUORI/$f" || { ko "scp di $f fallito"; exit 2; }
	done
	ok "quattro file → $FUORI/  (03-solo.py compreso: la finestra esclusiva vuole tutt'e due le macchine)"
	exit 0 ;;

costruisci)
	log "make, dentro il contenitore, nell'albero 03-b17-src"
	dentro "cd $DENTRO/03-b17-src/src && bash costruisci.sh"
	exit $? ;;

terreno)
	# ⛔⭐ QUI LA PAROLA RESTA SU CHUWI, e non e' un dettaglio: **il browser sta
	#     su CHUWI**, quindi e' il banco di QUESTA macchina che deve leggerla.
	#     Negli altri step il cliente girava dentro il contenitore e la parola
	#     andava di la'.
	log "La parola d'ordine, in un file 0600 su CHUWI (difetto D12)"
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
	mkdir -p "$LAVORO_QUI" || exit 2
	umask 077
	printf '%s' "$PW" > "$PAROLA_QUI"
	chmod 600 "$PAROLA_QUI"
	ls -l "$PAROLA_QUI"
	ok "la parola e' su CHUWI, 0600, e mai in un argv"
	exit 0 ;;

scena-costruisci)
	log "La scena dello step 2, costruita DENTRO il contenitore"
	dentro "SCENA_LAV=$DENTRO/03-b17-scena SCENA_C=$DENTRO/03-scena.c bash $DENTRO/03-b17-accendi.sh scena-costruisci"
	exit $? ;;

scena-avvia|scena-ferma|scena-conta|scena-uscite|ponte-accendi|ponte-ferma)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b17-accendi.sh $AZIONE ${2:-}"
	exit $? ;;

accendi|riaccendi|spegni|stato)
	# ⛔⛔ `D` SI PASSA DI LA', ED E' QUEL CHE RENDE POSSIBILE LA CORSIA E.
	#     `03-b17-accendi.sh` prende l'albero da `D` (binario + pagina), e la
	#     corsia E deve accendere lo STESSO prodotto da alberi diversi — quello
	#     software e quello con la codifica in hardware — senza cambiare una
	#     riga d'altro.  ⇒ `D=... sudo` non basta: `sudo` ripulisce l'ambiente,
	#     quindi la variabile va DOPO `sudo`.
	# ⚠ E l'albero si DICHIARA: `03-b17-accendi.sh` stampa l'impronta del
	#   binario e della pagina, ed e' quel che finisce nel verbale.
	fuori "sudo -S -p 'Password sudo: ' ${D:+D=\"$D\" }bash $FUORI/03-b17-accendi.sh $AZIONE"
	exit $? ;;

registro)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/03-b17-accendi.sh registro ${2:-60}"
	exit $? ;;

misura)
	SECONDI=${2:-25}
	RITARDI=${3:-0,25,60}
	# ⭐ Il GIRO si puo' nominare da fuori (`GIRO=A-software bash ... misura`):
	#    la corsia E ne fa tre di seguito — software, hardware, controllo — e
	#    tre nomi con dentro l'ora non direbbero QUALE era quale.  ⛔ E il nome
	#    finisce nel nome del verbale, che adesso e' uno per giro.
	NOME_GIRO=${GIRO:-b17-$(date +%Y%m%d-%H%M%S)}
	[ -f "$PAROLA_QUI" ] || { ko "⛔ manca $PAROLA_QUI: «terreno» prima"; exit 2; }
	# ⛔⭐ LA SCENA SI RIACCENDE PRIMA DI OGNI MISURA, E NON E' PRUDENZA.
	#     `[M]` 13 agosto 2026 (step 3): la scena resta VIVA ma smette di
	#     DISEGNARE quando nessuno registra piu' il suo monitor, e non riparte
	#     da sola.  ⇒ La misura dopo conterebbe zero con la catena perfetta.
	# ⚠ E si spegne PRIMA: il monitor virtuale del giro precedente non c'e'
	#   piu', e una scena attaccata a un monitor morto e' peggio di nessuna
	#   scena — sembra viva.
	bash "$0" scena-ferma >/dev/null 2>&1
	log "La misura — $SECONDI s per giro, ritardi noti «$RITARDI»"
	# ⛔⛔ `--verbale` NON SI PASSA PIU', ed e' la cura di un danno avvenuto.
	#     Qui c'era `--verbale "$LAVORO_QUI/verbale.json"`, un nome FISSO: ogni
	#     giro cancellava il precedente in silenzio, e dei quattordici giri del
	#     13 agosto 2026 ne e' sopravvissuto UNO.  ⇒ Adesso il nome lo fa il
	#     giro (`$LAVORO_QUI/verbali/verbale-<giro>.json`) e il banco RIFIUTA
	#     di sovrascriverne uno.  ⚠ `verbale-ultimo.json` resta come puntatore.
	# ⛔ I due GANCI: la scena si accende DOPO che la pagina ha dipinto il primo
	#    fotogramma, perche' prima il monitor virtuale del palco NON ESISTE (lo
	#    monta il figlio, non il server) e non c'e' nessun nome da chiedere.
	#    ⇒ Il banco li chiama al momento giusto, e non uno `sleep` prima.
	G_ON="python3 '$SSHPW' \"sudo -S -p 'Password sudo: ' bash $FUORI/03-b17-accendi.sh scena-avvia\""
	G_OFF="python3 '$SSHPW' \"sudo -S -p 'Password sudo: ' bash $FUORI/03-b17-accendi.sh scena-ferma\""
	python3 "$QUI/03-b17-ritardo.py" --misura \
		--host "$IND" --porta "$PORTA" --ancora "$ANCORA" \
		--comando-ponte "$LAV/comando" \
		--registro-prodotto "$LAV/registro.log" \
		--utente "$UTENTE" --parola-file "$PAROLA_QUI" \
		--secondi "$SECONDI" --ritardi "$RITARDI" \
		--schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
		--lavoro "$LAVORO_QUI" --giro "$NOME_GIRO" \
		--gancio-scena "$G_ON" --gancio-scena-spegni "$G_OFF" --p5
	exit $? ;;

esiti)
	tail -3 "$QUI/03-b17-esiti.jsonl" 2>/dev/null || ko "nessun esito depositato"
	exit 0 ;;

tutto)
	falle=0
	for passo in certifica porta costruisci terreno riaccendi scena-costruisci; do
		bash "$0" "$passo" || { ko "il passo «$passo» e' fallito"; exit 3; }
	done
	bash "$0" misura "${2:-25}" || falle=$((falle+1))
	printf '\n'
	[ "$falle" -eq 0 ] && ok "⭐ il giro intero e' passato" || ko "⛔ $falle rossi"
	exit "$falle" ;;

*)
	sed -n '2,30p' "$0"
	exit 2 ;;
esac
