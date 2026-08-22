#!/bin/bash
#
# 08-f3-sessione.sh — ⛔ GIRA SUL PORTATILE.  Il terreno dell'agente F3 della
# fase 8: una sessione VERA su cui leggere i quattro tratti del cliente sulla
# strada di disegno che il prodotto usa DAVVERO.
#
#   bash banchi/08-f3-sessione.sh porte      conta le porte, MIE e ALTRUI
#   bash banchi/08-f3-sessione.sh albero     l'albero mio, copiato da quello di B
#   bash banchi/08-f3-sessione.sh pagina     ⭐ solo `src/pagina.html`, senza `make`
#   bash banchi/08-f3-sessione.sh terreno    utente + sessione GNOME
#   bash banchi/08-f3-sessione.sh accendi    il prodotto sulla 7770
#   bash banchi/08-f3-sessione.sh aggancia   una sessione breve (il monitor nasce col figlio)
#   bash banchi/08-f3-sessione.sh scena-avvia | scena-ferma
#   bash banchi/08-f3-sessione.sh tratti [secondi] [strada]  ⭐⭐ LA MISURA
#   bash banchi/08-f3-sessione.sh elastico [secondi]         ⭐ il metro finale
#   bash banchi/08-f3-sessione.sh stato | registro | spegni
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ISOLAMENTO — `LEZIONI.md` §1.24: due banchi sulla stessa porta si
#     ammazzano in silenzio, e il rosso compare sul terzo.
#
#   MIE       7770 (il prodotto) · 7771-72 (ponte e ancora)
#   utente    provaf3 (uid 1047)  ⛔ e NON `prova`: `SPECIFICHE.md` §5.1 da' una
#                                    sola sessione grafica per utente, e `prova`
#                                    e' quella dove l'utente lavora
#   albero    /media/REMOTIX/src/08-f-src     lavoro /media/REMOTIX/tmp/08-f
#   scena     /dev/shm/remotix-08-f3
#
#   ⛔⛔ ALTRUI, SI CONTANO E NON SI TOCCANO:
#         **7730 e 7731** — i due server dell'UTENTE, e li sta usando ADESSO.
#         7740-7742 · 7746 · 7750 · 7752 · 7753 — altri agenti di questa fase.
#
#   ⚠ La 7770 e' stata CONTATA con `ss -tulnp` prima di prenderla, non dedotta
#     dal mandato: e' la sola ragione per cui questo banco non ammazza nessuno.
#
# ⭐ E L'ALBERO SI COPIA INVECE DI RICOMPILARLO, con la ragione: `src/main.c`
#   legge `pagina.html` **da disco**, non lo ha dentro il binario.  ⇒ Cambiare
#   la pagina non chiede un `make`, chiede uno `scp` e un riavvio del server.
#   ⛔ E il binario copiato e' quello di B, cioe' dello STESSO commit: se un
#     giorno gli alberi divergessero, questa riga diventerebbe la forma D5 —
#     «un binario stantio resta verde».  Per questo `albero` lo ricontrolla.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)

MACCHINA=${MACCHINA:-192.168.0.2}
IND=${IND:-192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}

PORTA=${PORTA:-7770}
PORTA_PONTE=${PORTA_PONTE:-7771}
PORTA_ANCORA=${PORTA_ANCORA:-7772}
UTENTE=${UTENTE:-provaf3}
UID_F=${UID_F:-1047}
PAROLA_UTENTE=${PAROLA_UTENTE:-provaf3-2026}

FUORI=/media/REMOTIX/src
ALBERO=$FUORI/08-f-src
DONATORE=${DONATORE:-$FUORI/08-b-src}
LAV=${LAV:-/media/REMOTIX/tmp/08-f}
SCENA_LAV=${SCENA_LAV:-$FUORI/08-f-scena-lav}
SCENA_DONATORE=${SCENA_DONATORE:-$FUORI/08-b-scena-lav}
SHM=${SHM:-remotix-08-f3}
TERRENO=$ALBERO/banchi/04-b32-terreno.sh

PAROLA_QUI=${PAROLA_QUI:-/tmp/08-f3/parola}
LAVORO_QUI=${LAVORO_QUI:-/tmp/08-f3}
SCHERMO=${SCHERMO:-:92}
DIAGNOSI=${DIAGNOSI:-9692}

AMB="PORTA=$PORTA_PONTE PORTA_DENTRO=$PORTA PORTA_ANCORA=$PORTA_ANCORA \
IND=$IND UTENTE=$UTENTE UID_B=$UID_F PAROLA=$PAROLA_UTENTE \
D=$ALBERO/src LAV=$LAV SCENA_LAV=$SCENA_LAV SCENA_C=$FUORI/04-b30-scena.c \
SHM=$SHM"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ MAI una redirezione ATTORNO a `ssh`: la richiesta della parola di `sudo` va
#    sullo stderr, e una redirezione la mangia.
fuori()  { timeout 900 ssh -o BatchMode=yes "$MACCHINA" "$1"; }
radice() { timeout 900 ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $AMB bash $TERRENO $1"; }

porte()
{
	log "Le porte — ⛔ MIE e ALTRUI, e le altrui si CONTANO e non si toccano"
	fuori "ss -tuln" | awk '{print $5}' | grep -oE ':(7[0-9]{3})$' \
	    | sort -u | sed 's/^/        /'
	inf "mie: $PORTA (prodotto) · $PORTA_PONTE-$PORTA_ANCORA (di riserva)"
	inf "⛔⛔ ALTRUI: 7730 e 7731 sono i server dell'UTENTE, e li sta usando"
	# ⛔ E QUI SI CONFRONTA, non si stampa soltanto (`LEZIONI.md` §1.20).
	if fuori "ss -tuln" | grep -qE ":$PORTA\b"; then
		ko "⛔ la $PORTA E' GIA' OCCUPATA: non la prendo"
		return 1
	fi
	ok "la $PORTA e' libera"
}

dentro() { timeout 1800 ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \"$1\""; }

porta()
{
	log "1a · I SORGENTI DI QUESTO ALBERO — ⛔ e non quelli di un altro agente"
	# ⛔⛔ E LA RAGIONE STA IN UN ROSSO DI OGGI: `albero` ha rifiutato di
	#     copiare il binario di B perche' `[M]` `cattura.c`, `codificatore.c` e
	#     `figlio.c` (piu' i loro `.h`) **sono diversi** — sono i file
	#     dell'agente C, che nel mio ramo non ci sono.  ⇒ Quel binario e' un
	#     ALTRO prodotto, e un numero preso li' sarebbe di un altro prodotto.
	#     ⭐ Il controllo e' servito la prima volta che e' stato eseguito.
	tar -C "$RADICE" --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/04-b32-terreno.sh banchi/04-b30-ponte.py \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/03-marca.py banchi/03-b17-ritardo.py banchi/03-solo.py \
		banchi/04-b30-anello-input.py banchi/04-b30-scena.c \
		banchi/08-b67-elastico.py banchi/08-b67-locale.py \
		banchi/08-f3-tratti.py \
	| ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $ALBERO && tar -C $ALBERO -xzf -" \
	|| { ko "⛔ i sorgenti non sono arrivati"; return 1; }
	ok "sorgenti in $ALBERO"
	scp -q -o BatchMode=yes "$QUI/04-b30-scena.c" "$MACCHINA:$FUORI/04-b30-scena.c" \
		|| { ko "⛔ la scena non e' arrivata"; return 1; }
	ok "la scena di A10 e' in $FUORI — ⛔ NON e' una copia mia"
}

costruisci()
{
	log "1b · Compilo il prodotto DENTRO il contenitore, nel MIO albero"
	dentro "PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 \
NGHTTP3=/srv/src/b2/nghttp3 bash /srv/src/08-f-src/src/costruisci.sh 2>&1 | tail -25"
}

scena()
{
	log "1c · La scena — ⛔ quella di A10, presa in prestito e non ricopiata"
	fuori "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \
'rm -rf $SCENA_LAV && cp -a $SCENA_DONATORE $SCENA_LAV && \
chmod 755 $SCENA_LAV $SCENA_LAV/* && mkdir -p $LAV && ls -l $SCENA_LAV/04-b30-scena'"
}

albero()
{
	log "1 · L'ALBERO MIO — una copia di quello di B, binario compreso"
	# ⛔ E si CONTROLLA che i sorgenti del donatore siano quelli di questo
	#    albero: se divergessero, il binario copiato sarebbe di un altro
	#    programma e ogni numero sarebbe preso su un prodotto che non e' questo.
	local mio suo
	mio=$(cd "$RADICE" && cat src/*.c src/*.h | sha256sum | cut -c1-16)
	suo=$(fuori "cat $DONATORE/src/*.c $DONATORE/src/*.h | sha256sum | cut -c1-16")
	inf "impronta dei sorgenti · qui $mio · donatore $suo"
	if [ "$mio" != "$suo" ]; then
		ko "⛔ i sorgenti C di $DONATORE NON sono quelli di questo albero: il "
		ko "   binario copiato sarebbe di un altro programma (forma D5).  Mi fermo."
		return 1
	fi
	ok "i sorgenti C combaciano: il binario del donatore e' di QUESTO commit"
	fuori "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \
'rm -rf $ALBERO && cp -a $DONATORE $ALBERO && rm -rf $SCENA_LAV && \
cp -a $SCENA_DONATORE $SCENA_LAV && chmod 755 $SCENA_LAV $SCENA_LAV/* && \
mkdir -p $LAV && ls -l $ALBERO/src/remotix'" || return 1
	ok "albero in $ALBERO · scena in $SCENA_LAV"
}

pagina()
{
	log '2 · ⭐ SOLO «pagina.html» — niente «make»: il server la legge da disco'
	scp -q -o BatchMode=yes "$RADICE/src/pagina.html" \
		"$MACCHINA:/tmp/08-f3-pagina.html" || { ko "⛔ non e' arrivata"; return 1; }
	fuori "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \
'cp /tmp/08-f3-pagina.html $ALBERO/src/pagina.html && \
chmod 644 $ALBERO/src/pagina.html && \
grep -c REMOTIX.tratti $ALBERO/src/pagina.html'" || return 1
	ok "pagina.html aggiornata (e la riga di `REMOTIX.tratti` c'e')"
}

terreno()
{
	log "3 · IL TERRENO — l'utente del banco e la sua sessione GNOME"
	radice utente   || return 1
	radice sessione || return 1
	mkdir -p "$LAVORO_QUI" || return 1
	# ⛔ D12: la parola sta in un file 0600 sul PORTATILE, e da `argv` non passa.
	umask 077
	printf '%s' "$PAROLA_UTENTE" > "$PAROLA_QUI"
	chmod 600 "$PAROLA_QUI"
	ok "la parola dell'utente del banco e' qui, 0600, e mai in un argv"
}

accendi()     { log "4 · Il prodotto sulla $PORTA"; radice accendi; }
scena_avvia() { log "La scena SUL MONITOR CATTURATO"; radice "scena-avvia ${1:-}"; }
scena_ferma() { radice scena-ferma; }
stato()       { radice stato; }
registro()    { radice "registro ${1:-80}"; }
spegni()      { log "Spengo — ⛔ SOLO le mie cose"; radice spegni; }

aggancia()
{
	log "5 · ⭐ UNA SESSIONE BREVE — il monitor virtuale nasce col FIGLIO"
	python3 -u "$QUI/08-b67-elastico.py" --misura --host "$IND" --porta "$PORTA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" --secondi 3 \
	    --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" --lavoro "$LAVORO_QUI" \
	    --giro "f3-aggancio"
	inf "⚠ qui NON conta il verdetto: conta che la sessione ci sia"
	return 0
}

tratti()
{
	log "6 · ⭐⭐ I QUATTRO TRATTI DEL CLIENTE, sulla strada ${2:-vera}"
	python3 -u "$QUI/08-f3-tratti.py" --host "$IND" --porta "$PORTA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" \
	    --secondi "${1:-30}" --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
	    --lavoro "$LAVORO_QUI" ${2:+--coda-url "$2"} \
	    --giro "${GIRO:-f3-$(date +%Y%m%d-%H%M%S)}"
}

elastico()
{
	log '7 · ⭐ IL METRO FINALE — «08-b67-elastico.py», il banco di B, NON toccato'
	python3 -u "$QUI/08-b67-elastico.py" --misura --host "$IND" --porta "$PORTA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" \
	    --secondi "${1:-25}" --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
	    --lavoro "$LAVORO_QUI" --giro "${GIRO:-f3-elastico-$(date +%H%M%S)}"
	u=$?
	case $u in
	0) ok  "CONFORME" ;;
	1) ko  "NON CONFORME" ;;
	3) ko  "⛔ NON HO NIENTE DA GIUDICARE — e NON e' «conforme»" ;;
	*) ko  "uscita $u" ;;
	esac
	return $u
}

case "${1:-}" in
porte)       porte ;;
porta)       porta ;;
costruisci)  costruisci ;;
scena)       scena ;;
albero)      albero ;;
pagina)      pagina ;;
terreno)     terreno ;;
accendi)     accendi ;;
aggancia)    aggancia ;;
scena-avvia) scena_avvia "${2:-}" ;;
scena-ferma) scena_ferma ;;
tratti)      tratti "${2:-30}" "${3:-}" ;;
elastico)    elastico "${2:-25}" ;;
stato)       stato ;;
registro)    registro "${2:-80}" ;;
spegni)      spegni ;;
*)           sed -n '2,20p' "$0"; exit 2 ;;
esac
