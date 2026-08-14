#!/bin/bash
#
# 04-b30-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco A10 della fase 4:
# ⭐⭐ L'ANELLO **INPUT → VETRO**.
#
#   bash banchi/04-b30-lancia.sh certifica   ⭐ gira QUI, senza rete e senza server
#   bash banchi/04-b30-lancia.sh finto       ⭐ che cosa dira' quando il prodotto arriva
#   bash banchi/04-b30-lancia.sh porte       conta le porte, MIE e ALTRUI
#   bash banchi/04-b30-lancia.sh porta       copia src/ e i banchi sulla macchina
#   bash banchi/04-b30-lancia.sh costruisci  `make` dentro il contenitore
#   bash banchi/04-b30-lancia.sh scena-costruisci
#   bash banchi/04-b30-lancia.sh terreno     ⭐ utente, sessione e parola
#   bash banchi/04-b30-lancia.sh accendi     prodotto (7722) + ponte (7721+7723)
#   bash banchi/04-b30-lancia.sh misura [secondi]
#   bash banchi/04-b30-lancia.sh stato | registro | spegni | esiti
#   bash banchi/04-b30-lancia.sh tutto
#
# ⛔⛔ LE PORTE SONO CAMBIATE — 14 agosto 2026, sera.
#    Erano 7691-95 (l'anello A10 della mattina).  L'anello **O2** che riprende
#    il lavoro ha 7721-25, e le due serie NON si mescolano: se un giorno il
#    banco di A10 fosse ancora acceso su 7691, questo non lo tocca.
#
# ---------------------------------------------------------------------------
# ⛔ LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, E CIASCUNA E' STATA PAGATA
#
#   · ⛔ **MAI una redirezione ATTORNO a `ssh` o a `enter.sh`** — pagata SEI
#     volte: la richiesta della parola di `sudo` va sullo stderr, e una
#     redirezione la mangia.  ⇒ Si passa da `v1/strumenti/sshpw.py`;
#   · ⛔ **un file non ha livelli di virgolette**: quel che deve girare sul
#     server sta in uno SCRIPT, non dentro `ssh → enter.sh → bash -c`;
#   · ⛔ **niente `set -e`**: si contano i rossi e si va avanti.
#
# ---------------------------------------------------------------------------
# ⛔⛔ LE PORTE, E LA CONVIVENZA CON GLI ALTRI NOVE ANELLI
#
#   MIE       7721 (il browser)  ·  7722 (il prodotto, dietro il ponte)
#             7723 (l'ancora dell'orologio)  ·  7724-25 di riserva
#   ⛔ ALTRUI, e non si toccano:
#             7448 · 7501 · 7561  (dell'utente)
#             7571                (l'albero del deposito, lasciato acceso apposta)
#             7700                ⛔⛔ **L'UTENTE CI STA LAVORANDO ADESSO**
#             7601-05 A1 · 7611-15 A2 · 7621-25 A3 · 7631-35 A4 · 7641-45 A5
#             7651-55 A6 · 7661-65 A7 · 7671-75 A8 · 7681-85 A9 · 7691-95 A10
#
# ⭐ E il ban-file e il socket dei comandi sono MIEI: un ban condiviso fra dieci
#   banchi e' un banco che ferma gli altri nove.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/v1/strumenti/sshpw.py"
FUORI=/media/REMOTIX/src
ALBERO=$FUORI/04-b30-src
DENTRO=/srv/src
TERRENO=$FUORI/04-b32-terreno.sh
PORTA=7721
PORTA_DENTRO=7722
ANCORA=7723
IND=${IND:-192.168.0.2}
LAV=/media/REMOTIX/tmp/04-b30
# ⛔ L'utente e' quello DEL BANCO, non `nicfio`: `SPECIFICHE.md` §5.1 da' una
#    sola sessione grafica per utente, e `nicfio`, `prova` (dove l'utente sta
#    lavorando ADESSO) e `provaa1` (il banco A1) ce l'hanno gia'.
UTENTE=${UTENTE:-provao2}
PAROLA=${PAROLA:-provao2-2026}
PAROLA_QUI=${PAROLA_QUI:-/tmp/04-b30/parola}
LAVORO_QUI=${LAVORO_QUI:-/tmp/04-b30}
SCHERMO=${SCHERMO:-:90}
DIAGNOSI=${DIAGNOSI:-9630}
# ⛔ MIEI, e con il numero della porta dentro: due banchi che condividessero il
#    ban-file si bannerebbero a vicenda, e il rosso comparirebbe sul terzo.
BAN=$LAV/ban-$PORTA_DENTRO
SOCK=$LAV/comando-$PORTA_DENTRO.sock
# ⭐ La scena: nome di shm MIO, o due scene si sovrascrivono lo stato a vicenda
#    e i conti dell'input diventano la somma di due banchi.
SHM=remotix-04-b30

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

# ═══════════════════════════════════════════════════════════════════════════
certifica()
{
	log "⭐ LA CERTIFICAZIONE — gira QUI, senza rete e senza server"
	inf "⛔ `CODER.md` §3.3: il banco si certifica PRIMA di essere puntato"
	inf "   sull'incognita, o un rosso e' ambiguo fra il prodotto e lo strumento."
	python3 "$QUI/04-b30-anello-input.py" --certifica
	return $?
}

finto()
{
	log "⭐ IL FINTO — che cosa il banco DIRA' quando il prodotto arriva"
	inf "⛔ Nessuno di questi numeri e' una misura: sono la FORMA della misura."
	python3 "$QUI/04-b30-anello-input.py" --finto
	return $?
}

porte()
{
	log "Le porte — ⛔ MIE e ALTRUI, e le altrui si CONTANO e non si toccano"
	fuori "ss -tuln"  | awk '{print $5}' | grep -oE ':(7[0-9]{3})$' \
	    | sort -u | sed 's/^/        /'
	inf "mie: $PORTA (browser) · $PORTA_DENTRO (prodotto) · $ANCORA (ancora)"
	inf "⛔ altrui, mai toccate: 7448 · 7501 · 7561 · 7571 · 7601-7685"
}

porta()
{
	log "1. I sorgenti del prodotto, in un albero MIO (una COPIA)"
	# ⛔ Il gemello di `rcp.c` va con loro: `costruisci.sh` li confronta, e senza
	#    il confronto si costruirebbe un binario che nessuno ha guardato.
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO $LAV" || return 1
	tar czf /tmp/04-b30-src.tgz -C "$RADICE" src banchi/rcp || { ko "tar fallito"; return 1; }
	metti /tmp/04-b30-src.tgz "$ALBERO/src.tgz" || return 1
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/input.c src/pagina.html banchi/rcp/rcp.c" || return 1
	log "2. E i banchi, accanto agli altri"
	for f in 04-b30-anello-input.py 04-b30-ponte.py 04-b30-scena.c \
	         04-b32-terreno.sh \
	         03-marca.py 03-b17-ritardo.py 03-solo.py 02-pagina-misura-cdp.py; do
		metti "$QUI/$f" "$FUORI/$f" || return 1
	done
	ok "sorgenti e banchi portati"
}

costruisci()
{
	log "Costruisco il prodotto DENTRO il contenitore, nell'albero 04-b30-src"
	# ⛔ Il percorso ha l'albero dentro: `$DENTRO` da solo e' la cartella DEI
	#    BANCHI, e un `make` li' dentro non costruirebbe niente di mio.
	dentro "cd $DENTRO/04-b30-src/src && bash costruisci.sh"
	return $?
}

scena_costruisci()
{
	log "Costruisco LA SCENA CHE RISPONDE ALL'INPUT (04-b30-scena.c)"
	# ⛔ Si compila su un nome nuovo e poi si rinomina: il nucleo rifiuta di
	#    scrivere su un eseguibile in esecuzione (ETXTBSY) e `gcc -o` lascia
	#    un binario TRONCATO — cioe' un banco che parte e non si sa che cosa
	#    esegue.  E' la lezione di `03-scena-accendi.sh`.
	# ⛔ E la cartella sta sotto `$DENTRO`, non sotto `$LAV`: dentro il
	#    contenitore `/media/REMOTIX/tmp` NON ESISTE (e' montato solo
	#    `/media/REMOTIX/src` su `/srv/src`), e un `mkdir` li' dentro
	#    fallirebbe in silenzio.
	dentro "set -u
	P=/usr/share/wayland-protocols
	L=$DENTRO/04-b30-scena-lav
	mkdir -p \$L
	cd \$L
	wayland-scanner client-header \$P/stable/xdg-shell/xdg-shell.xml xdg-shell-client-protocol.h
	wayland-scanner private-code  \$P/stable/xdg-shell/xdg-shell.xml xdg-shell-protocol.c
	wayland-scanner client-header \$P/stable/presentation-time/presentation-time.xml presentation-time-client-protocol.h
	wayland-scanner private-code  \$P/stable/presentation-time/presentation-time.xml presentation-time-protocol.c
	gcc -O2 -Wall -Wextra -o \$L/scena.nuovo $DENTRO/04-b30-scena.c \\
	    \$L/xdg-shell-protocol.c \$L/presentation-time-protocol.c \\
	    -I\$L \$(pkg-config --cflags --libs wayland-client) -lrt
	mv -f \$L/scena.nuovo \$L/04-b30-scena
	chmod 755 \$L \$L/04-b30-scena
	echo COSTRUITA"
	return $?
}

terreno()
{
	log "⭐ IL TERRENO — l'utente del banco, la sua sessione, e la parola QUI"
	# ⛔ La parola resta su CHUWI e in un file 0600: **il browser sta qui**,
	#    quindi e' il banco di QUESTA macchina che deve leggerla, e da `argv`
	#    non ci passa mai (difetto D12).
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO utente" || return 1
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO sessione" || return 1
	mkdir -p "$LAVORO_QUI" || return 1
	umask 077
	printf '%s' "$PAROLA" > "$PAROLA_QUI"
	chmod 600 "$PAROLA_QUI"
	ls -l "$PAROLA_QUI"
	ok "la parola dell'utente del banco e' su CHUWI, 0600, e mai in un argv"
}

accendi()
{
	log "⭐ ACCENDO: prodotto ($PORTA_DENTRO) + ponte ($PORTA + $ANCORA)"
	# ⛔ La scena NON si accende qui: la accende la MISURA, dopo che qualcuno e'
	#    entrato nella sessione.  Il monitor virtuale nasce col FIGLIO, non col
	#    server, e una scena accesa prima finirebbe «da qualche parte».
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO accendi" || return 1
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO ponte-accendi" || return 1
}

stato()
{
	log "Lo stato"
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO stato"
}

registro() { fuori "sudo -S -p 'Password sudo: ' bash $TERRENO registro ${1:-60}"; }

spegni()
{
	log "Spengo — ⛔ SOLO le mie cose"
	fuori "sudo -S -p 'Password sudo: ' bash $TERRENO spegni"
	ok "spente le mie; ⛔ le porte altrui non sono state toccate"
}

esiti() { tail -5 "$QUI/04-b30-esiti.jsonl" 2>/dev/null || inf "(nessun esito)"; }

misura()
{
	log "LA MISURA"
	# ⛔ `-u`: senza, la stampa resta nel buffer finche' il giro non finisce, e
	#    un giro di due minuti sembra un banco appeso.  ⚠ E chi guarda un banco
	#    appeso lo ammazza — perdendo la misura invece del difetto.
	python3 -u "$QUI/04-b30-anello-input.py" --misura --host "$IND" \
	    --porta "$PORTA" --porta-dentro "$PORTA_DENTRO" --ancora "$ANCORA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" \
	    --secondi "${1:-45}" --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
	    --lavoro "$LAVORO_QUI" --shm-scena "/dev/shm/$SHM" \
	    --comando-ponte "$LAV/comando" --terreno "$TERRENO" \
	    --registro-prodotto "$LAV/registro.log" \
	    --verbale-ponte "$LAV/ponte.json" \
	    --giro "${GIRO:-b30-$(date +%Y%m%d-%H%M%S)}" \
	    ${MANI:+--mani $MANI} ${PASSO_MS:+--passo-ms $PASSO_MS}
	u=$?
	# ⛔⛔ E IL CODICE 3 SI RIPORTA, non si schiaccia su 0.  E' il difetto del
	#     validatore della fase 1: usciva «conforme» avendo giudicato zero cose.
	case $u in
	0) ok  "CONFORME" ;;
	1) ko  "NON CONFORME — il banco ha guardato e ha trovato un rosso" ;;
	3) ko  "⛔ NON HO NIENTE DA GIUDICARE — e NON e' «conforme»" ;;
	*) ko  "uscita $u" ;;
	esac
	return $u
}

case "${1:-}" in
certifica)        certifica ;;
finto)            finto ;;
porte)            porte ;;
porta)            porta ;;
costruisci)       costruisci ;;
scena-costruisci) scena_costruisci ;;
terreno)          terreno ;;
accendi)          accendi ;;
scena-avvia)      fuori "sudo -S -p 'Password sudo: ' bash $TERRENO scena-avvia ${2:-}" ;;
scena-ferma)      fuori "sudo -S -p 'Password sudo: ' bash $TERRENO scena-ferma" ;;
misura)           misura "${2:-45}" ;;
stato)            stato ;;
registro)         registro "${2:-60}" ;;
spegni)           spegni ;;
esiti)            esiti ;;
tutto)            certifica && finto && porte ;;
*)                sed -n '2,25p' "$0" ; exit 2 ;;
esac
