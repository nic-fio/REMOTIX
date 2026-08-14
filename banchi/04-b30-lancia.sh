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
#   bash banchi/04-b30-lancia.sh accendi     prodotto (7692) + ponte (7691+7693)
#   bash banchi/04-b30-lancia.sh misura [secondi]
#   bash banchi/04-b30-lancia.sh stato | registro | spegni | esiti
#   bash banchi/04-b30-lancia.sh tutto
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
#   MIE       7691 (il browser)  ·  7692 (il prodotto, dietro il ponte)
#             7693 (l'ancora dell'orologio)  ·  7694-95 di riserva
#   ⛔ ALTRUI, e non si toccano:
#             7448 · 7501 · 7561  (dell'utente)
#             7571                (l'albero del deposito, lasciato acceso apposta)
#             7601-05 A1 · 7611-15 A2 · 7621-25 A3 · 7631-35 A4 · 7641-45 A5
#             7651-55 A6 · 7661-65 A7 · 7671-75 A8 · 7681-85 A9
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
PORTA=7691
PORTA_DENTRO=7692
ANCORA=7693
IND=${IND:-192.168.0.2}
LAV=/media/REMOTIX/tmp/04-b30
UTENTE=${UTENTE:-nicfio}
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
	log "Porto i sorgenti e i banchi sulla macchina"
	fuori "mkdir -p $ALBERO $LAV" || return 1
	for f in "$RADICE"/src/*.c "$RADICE"/src/*.h "$RADICE"/src/Makefile \
	         "$RADICE"/src/pagina.html; do
		metti "$f" "$ALBERO/$(basename "$f")" || return 1
	done
	for f in 04-b30-anello-input.py 04-b30-ponte.py 04-b30-scena.c \
	         03-marca.py 03-b17-ritardo.py 03-solo.py 02-pagina-misura-cdp.py; do
		metti "$QUI/$f" "$FUORI/$f" || return 1
	done
	ok "sorgenti e banchi portati"
}

costruisci()
{
	log "Costruisco il prodotto DENTRO il contenitore"
	dentro "cd $DENTRO && make -j4"
	return $?
}

scena_costruisci()
{
	log "Costruisco LA SCENA CHE RISPONDE ALL'INPUT (04-b30-scena.c)"
	# ⛔ Si compila su un nome nuovo e poi si rinomina: il nucleo rifiuta di
	#    scrivere su un eseguibile in esecuzione (ETXTBSY) e `gcc -o` lascia
	#    un binario TRONCATO — cioe' un banco che parte e non si sa che cosa
	#    esegue.  E' la lezione di `03-scena-accendi.sh`.
	dentro "set -u
	P=/usr/share/wayland-protocols
	L=$LAV/scena
	mkdir -p \$L
	wayland-scanner client-header \$P/stable/xdg-shell/xdg-shell.xml \$L/xdg-shell-client-protocol.h
	wayland-scanner private-code  \$P/stable/xdg-shell/xdg-shell.xml \$L/xdg-shell-protocol.c
	wayland-scanner client-header \$P/stable/presentation-time/presentation-time.xml \$L/presentation-time-client-protocol.h
	wayland-scanner private-code  \$P/stable/presentation-time/presentation-time.xml \$L/presentation-time-protocol.c
	gcc -O2 -Wall -Wextra -o \$L/scena.nuovo $FUORI/04-b30-scena.c \\
	    \$L/xdg-shell-protocol.c \$L/presentation-time-protocol.c \\
	    -I\$L \$(pkg-config --cflags --libs wayland-client) -lrt
	mv -f \$L/scena.nuovo \$L/04-b30-scena
	\$L/04-b30-scena --uscite 2>&1 | head -20"
	return $?
}

stato()
{
	log "Lo stato"
	fuori "ss -tuln | grep -E ':($PORTA|$PORTA_DENTRO|$ANCORA)\b' || echo '(nessuna delle mie porte ascolta)'"
	fuori "ls -la $LAV 2>/dev/null | head -20"
	inf "⛔ e il blocco della scena, che dice se l'input ARRIVA AL DESKTOP:"
	fuori "python3 $FUORI/04-b30-anello-input.py --verdetto /dev/null 2>&1 | head -3 || true"
}

registro() { fuori "tail -60 $LAV/registro.log"; }

spegni()
{
	log "Spengo — ⛔ SOLO le mie cose"
	fuori "pkill -f 'porta $PORTA_DENTRO' ; pkill -f '04-b30-ponte' ; pkill -f '04-b30-scena' ; true"
	ok "spente le mie; ⛔ le porte altrui non sono state toccate"
}

esiti() { tail -5 "$QUI/04-b30-esiti.jsonl" 2>/dev/null || inf "(nessun esito)"; }

misura()
{
	log "LA MISURA"
	python3 "$QUI/04-b30-anello-input.py" --misura --host "$IND" \
	    --porta "$PORTA" --porta-dentro "$PORTA_DENTRO" --ancora "$ANCORA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" \
	    --secondi "${1:-25}" --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
	    --lavoro "$LAVORO_QUI" --shm-scena "/dev/shm/$SHM"
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
accendi)          ko "⛔ da scrivere quando il canale di input c'e': oggi il"
                  ko "   prodotto non ha ancora l'iniezione, e accendere un"
                  ko "   giro che non puo' chiudere l'anello produrrebbe un"
                  ko "   verbale vuoto con l'aria di una misura." ; exit 3 ;;
misura)           misura "${2:-25}" ;;
stato)            stato ;;
registro)         registro ;;
spegni)           spegni ;;
esiti)            esiti ;;
tutto)            certifica && finto && porte ;;
*)                sed -n '2,25p' "$0" ; exit 2 ;;
esac
