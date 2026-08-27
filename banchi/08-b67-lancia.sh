#!/bin/bash
#
# 08-b67-lancia.sh — ⛔ GIRA SUL PORTATILE.  Il banco del TRASCINAMENTO,
# fase 8, agente B.
#
#   bash banchi/08-b67-lancia.sh certifica   ⭐ gira QUI, senza rete e senza server
#   bash banchi/08-b67-lancia.sh finto       che cosa dira' quando il prodotto arriva
#   bash banchi/08-b67-lancia.sh porte       conta le porte, MIE e ALTRUI
#   bash banchi/08-b67-lancia.sh porta       copia src/ e i banchi sulla macchina
#   bash banchi/08-b67-lancia.sh costruisci  `make` dentro il contenitore
#   bash banchi/08-b67-lancia.sh scena-costruisci
#   bash banchi/08-b67-lancia.sh terreno     utente + sessione GNOME
#   bash banchi/08-b67-lancia.sh accendi     il prodotto sulla 7746
#   bash banchi/08-b67-lancia.sh aggancia    ⭐ una sessione breve: il MONITOR
#                                            VIRTUALE nasce col figlio, non col
#                                            server — senza, la scena finirebbe
#                                            «da qualche parte»
#   bash banchi/08-b67-lancia.sh scena-avvia
#   bash banchi/08-b67-lancia.sh misura [secondi]
#   bash banchi/08-b67-lancia.sh stato | registro | scena-ferma | spegni
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ISOLAMENTO — `LEZIONI.md` §1.24: due banchi sulla stessa porta si
#     ammazzano in silenzio, e il rosso compare sul terzo.
#
#   MIE       7746 (il prodotto)  ·  7747-48 (il ponte e l'ancora, se servono)
#   utente    provab8 (uid 1043)     ⛔ e NON `prova`: `SPECIFICHE.md` §5.1 da'
#                                       una sola sessione grafica per utente, e
#                                       `prova` e' quella dove l'utente lavora
#   albero    /media/REMOTIX/src/08-b-src
#   lavoro    /media/REMOTIX/tmp/08-b   (ban-file, socket di comando, registro)
#   scena     /dev/shm/remotix-08-b
#
#   ⛔⛔ ALTRUI, SI CONTANO E NON SI TOCCANO:
#         **7730 e 7731** — ⛔ i due server dell'UTENTE, e li sta usando ADESSO.
#         7700 · 7448 · 7501 · 7561 · 7571 · 7601-7685 · 7801
#
# ⛔⛔⛔ E LA 7741 NON E' LIBERA — misurato il 22 agosto 2026, prima di toccarla.
#
#   Il mandato diceva *«la tua porta e' la 7741»*.  `[M]` `ss -tulnp` dice che
#   su quella porta c'e' gia'
#       /media/REMOTIX/src/08-a-src/src/remotix --porta 7741
#         --ban-file /media/REMOTIX/tmp/08-a/ban-7741
#   cioe' **il server dell'agente A di questa stessa fase**, con accanto il suo
#   ponte sulla 7740/7742.  ⇒ ⛔ Non la prendo e non la spengo: `LEZIONI.md`
#   §1.24 — due banchi sulla stessa porta si ammazzano in silenzio, e il rosso
#   compare sul terzo.  ⭐ E il ban-file e' il suo: un ban condiviso avrebbe
#   fermato lui per un errore mio.
#
#   ⚠ Le porte sono state CONTATE prima di scegliere, e non dedotte dal
#     mandato: e' la sola ragione per cui questo banco non ha ammazzato A.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL TERRENO NON E' SCRITTO QUI: si GUIDA `banchi/04-b32-terreno.sh`
#
# ⛔ Quel file e' il terreno dell'anello A10 della fase 4, e ogni sua variabile
#    e' gia' `${VAR:-difetto}`.  ⇒ Ricopiarlo per cambiare cinque numeri
#    vorrebbe dire mantenere due copie della stessa trappola — il drop-in di
#    sistema che impone `--virtual-monitor`, il gruppo `render` che vale 95 ms,
#    il congedo della sessione vecchia prima di aprirne una nuova.
# ⭐ Si guida con l'ambiente, e se un giorno quel file impara una trappola nuova
#   questo banco la eredita senza toccare niente.
#
# ⛔ E LE REGOLE DI CASA CHE QUESTO FILE RISPETTA, ciascuna pagata:
#   · MAI una redirezione ATTORNO a `ssh`: la richiesta della parola di `sudo`
#     va sullo stderr, e una redirezione la mangia (pagata sei volte);
#   · niente `set -e`: si contano i rossi e si va avanti;
#   · quel che deve girare sul server sta in uno SCRIPT gia' presente la',
#     non dentro `ssh → bash -c` a tre livelli di virgolette.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)

MACCHINA=${MACCHINA:-192.168.0.2}
IND=${IND:-192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}

PORTA=${PORTA:-7746}                 # ⭐ la MIA — ⛔ la 7741 e' di A
PORTA_PONTE=${PORTA_PONTE:-7747}
PORTA_ANCORA=${PORTA_ANCORA:-7748}
UTENTE=${UTENTE:-provab8}
UID_B=${UID_B:-1043}
PAROLA_UTENTE=${PAROLA_UTENTE:-provab8-2026}

FUORI=/media/REMOTIX/src
ALBERO=$FUORI/08-b-src
DENTRO=/srv/src
LAV=${LAV:-/media/REMOTIX/tmp/08-b}
SCENA_LAV=${SCENA_LAV:-$FUORI/08-b-scena-lav}
SHM=${SHM:-remotix-08-b}
TERRENO=$ALBERO/banchi/04-b32-terreno.sh

# Quel che gira sul portatile
PAROLA_QUI=${PAROLA_QUI:-/tmp/08-b67/parola}
LAVORO_QUI=${LAVORO_QUI:-/tmp/08-b67}
SCHERMO=${SCHERMO:-:88}
DIAGNOSI=${DIAGNOSI:-9641}

# ⛔ L'ambiente con cui si guida il terreno di A10.  Sta in UNA variabile: se
#    fosse ripetuto a ogni chiamata, il giorno in cui se ne cambia uno se ne
#    dimentica uno.
AMB="PORTA=$PORTA_PONTE PORTA_DENTRO=$PORTA PORTA_ANCORA=$PORTA_ANCORA \
IND=$IND UTENTE=$UTENTE UID_B=$UID_B PAROLA=$PAROLA_UTENTE \
D=$ALBERO/src LAV=$LAV SCENA_LAV=$SCENA_LAV SCENA_C=$FUORI/04-b30-scena.c \
SHM=$SHM"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 ssh -o BatchMode=yes "$MACCHINA" "$1"; }
radice() { timeout 900 ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $AMB bash $TERRENO $1"; }
dentro() { timeout 900 ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \"$1\""; }

# ═══════════════════════════════════════════════════════════════════════════
certifica() { python3 -u "$QUI/08-b67-elastico.py" --certifica; }
finto()     { python3 -u "$QUI/08-b67-elastico.py" --finto; }

porte()
{
	log "Le porte — ⛔ MIE e ALTRUI, e le altrui si CONTANO e non si toccano"
	fuori "ss -tuln" | awk '{print $5}' | grep -oE ':(7[0-9]{3})$' \
	    | sort -u | sed 's/^/        /'
	inf "mie: $PORTA (prodotto) · $PORTA_PONTE-$PORTA_ANCORA (di riserva)"
	inf "⛔⛔ ALTRUI: 7730 e 7731 sono i server dell'UTENTE, e li sta usando"
}

porta()
{
	log "1 · I sorgenti del prodotto, in un albero MIO (una COPIA)"
	# ⛔ Si esclude il binario del portatile e gli oggetti: spedendoli, `make`
	#    troverebbe tutto aggiornato e resterebbe il binario sbagliato — la
	#    forma D5, «un binario stantio resta verde».
	# ⛔ E `banchi/rcp` va con loro: il Makefile si rifiuta di compilare se non
	#    puo' confrontare le due copie di `rcp.c` (R12.3).
	tar -C "$RADICE" --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/attrezzi-gruppi-scheda.sh banchi/04-b32-terreno.sh banchi/04-b30-ponte.py \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/03-marca.py banchi/03-b17-ritardo.py banchi/03-solo.py \
		banchi/04-b30-anello-input.py banchi/04-b30-scena.c \
		banchi/08-b67-elastico.py banchi/08-b67-locale.py \
	| ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $ALBERO && tar -C $ALBERO -xzf -" \
	|| { ko "⛔ i sorgenti non sono arrivati"; return 1; }
	ok "sorgenti in $ALBERO"
	# ⛔ La scena si prende da A10 SENZA copiarla nel mio albero: e' la sua, e
	#    va usata quella.  Si porta solo dove il terreno la cerca.
	scp -q -o BatchMode=yes "$QUI/04-b30-scena.c" "$MACCHINA:$FUORI/04-b30-scena.c" \
		|| { ko "⛔ la scena non e' arrivata"; return 1; }
	ok "la scena di A10 (04-b30-scena.c) e' in $FUORI — ⛔ NON e' una copia mia"
}

costruisci()
{
	log "2 · Compilo il prodotto DENTRO il contenitore, nel MIO albero"
	dentro "PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 \
NGHTTP3=/srv/src/b2/nghttp3 bash $DENTRO/08-b-src/src/costruisci.sh 2>&1 | tail -20"
}

scena_costruisci()
{
	log "3 · Costruisco LA SCENA — ⛔ quella di A10, senza una riga cambiata"
	# ⛔ Si compila su un nome nuovo e poi si rinomina: il nucleo rifiuta di
	#    scrivere su un eseguibile in esecuzione (ETXTBSY) e `gcc -o` lascia un
	#    binario TRONCATO, cioe' un banco che parte e non si sa che cosa esegue.
	# ⛔⛔ NIENTE VARIABILI DI SHELL DENTRO QUESTA STRINGA, e la ragione e' un
	#    rosso gia' pagato oggi: il comando attraversa `ssh` → `sudo` →
	#    `enter.sh --root "…"`, cioe' **tre** livelli di virgolette.  `\$L`
	#    sopravvive al primo e muore al secondo, e `gcc` finisce a cercare
	#    `/xdg-shell-protocol.c`.  ⇒ ⭐ Il copione si SCRIVE su un file sulla
	#    macchina e li' dentro le variabili sono al sicuro (`04-b30-lancia.sh`:
	#    *«un file non ha livelli di virgolette»*).
	cat > /tmp/08-b67-scena.sh <<'FINE'
set -u
P=/usr/share/wayland-protocols
L=/srv/src/08-b-scena-lav
mkdir -p "$L" && cd "$L" || exit 2
wayland-scanner client-header "$P/stable/xdg-shell/xdg-shell.xml" xdg-shell-client-protocol.h || exit 2
wayland-scanner private-code  "$P/stable/xdg-shell/xdg-shell.xml" xdg-shell-protocol.c || exit 2
wayland-scanner client-header "$P/stable/presentation-time/presentation-time.xml" presentation-time-client-protocol.h || exit 2
wayland-scanner private-code  "$P/stable/presentation-time/presentation-time.xml" presentation-time-protocol.c || exit 2
# ⛔ Si compila su un nome NUOVO e poi si rinomina: `gcc -o` su un eseguibile in
#    esecuzione lascia un binario TRONCATO (ETXTBSY), cioe' un banco che parte e
#    non si sa che cosa esegue.
gcc -O2 -Wall -Wextra -o "$L/scena.nuovo" /srv/src/04-b30-scena.c \
    "$L/xdg-shell-protocol.c" "$L/presentation-time-protocol.c" \
    -I"$L" $(pkg-config --cflags --libs wayland-client) -lrt || exit 2
mv -f "$L/scena.nuovo" "$L/04-b30-scena" || exit 2
chmod 755 "$L" "$L/04-b30-scena"
ls -l "$L/04-b30-scena"
echo COSTRUITA
FINE
	scp -q -o BatchMode=yes /tmp/08-b67-scena.sh "$MACCHINA:$FUORI/08-b67-scena.sh" \
		|| { ko "⛔ il copione non e' arrivato"; return 1; }
	dentro "bash /srv/src/08-b67-scena.sh"
}

terreno()
{
	log "4 · IL TERRENO — l'utente del banco e la sua sessione GNOME"
	radice utente   || return 1
	radice sessione || return 1
	mkdir -p "$LAVORO_QUI" || return 1
	# ⛔ D12: la parola sta in un file 0600 sul PORTATILE (il browser sta qui) e
	#    da `argv` non ci passa mai.
	umask 077
	printf '%s' "$PAROLA_UTENTE" > "$PAROLA_QUI"
	chmod 600 "$PAROLA_QUI"
	ls -l "$PAROLA_QUI"
	ok "la parola dell'utente del banco e' qui, 0600, e mai in un argv"
}

accendi()      { log "5 · Il prodotto sulla $PORTA"; radice accendi; }
aggancia()
{
	log "6 · ⭐ UNA SESSIONE BREVE — il monitor virtuale nasce col FIGLIO"
	inf "⛔ La scena NON si accende prima: finirebbe «da qualche parte», e"
	inf "   sarebbe uno zero puntato sull'imputato sbagliato."
	inf "⚠ Il palco sopravvive al distacco (invariante I4), quindi tre secondi"
	inf "  bastano e la sessione resta in piedi per la misura."
	python3 -u "$QUI/08-b67-elastico.py" --misura --host "$IND" --porta "$PORTA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" --secondi 3 \
	    --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" --lavoro "$LAVORO_QUI" \
	    --giro "b67-aggancio"
	u=$?
	inf "l'aggancio e' uscito $u — ⚠ qui NON conta il verdetto: conta che la"
	inf "  sessione ci sia.  Il numero si prende al giro vero."
	return 0
}
scena_avvia()  { log "7 · La scena SUL MONITOR CATTURATO"; radice "scena-avvia ${1:-}"; }
scena_ferma()  { radice scena-ferma; }
stato()        { radice stato; }
registro()     { radice "registro ${1:-60}"; }
spegni()       { log "Spengo — ⛔ SOLO le mie cose"; radice spegni; }

misura()
{
	log "8 · LA MISURA — ⛔ il ping corre nello stesso giro"
	# ⛔ `-u`: senza, la stampa resta nel buffer finche' il giro non finisce, e
	#    un giro di un minuto sembra un banco appeso.  ⚠ Chi guarda un banco
	#    appeso lo ammazza, perdendo la misura invece del difetto.
	python3 -u "$QUI/08-b67-elastico.py" --misura --host "$IND" --porta "$PORTA" \
	    --utente "$UTENTE" --parola-file "$PAROLA_QUI" \
	    --secondi "${1:-25}" --schermo "$SCHERMO" --diagnosi "$DIAGNOSI" \
	    --lavoro "$LAVORO_QUI" --giro "${GIRO:-b67-$(date +%Y%m%d-%H%M%S)}" \
	    ${PASSO_MS:+--passo-ms $PASSO_MS} ${BARRA:+--barra $BARRA}
	u=$?
	# ⛔⛔ E IL CODICE 3 SI RIPORTA, non si schiaccia su 0.
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
aggancia)         aggancia ;;
scena-avvia)      scena_avvia "${2:-}" ;;
scena-ferma)      scena_ferma ;;
misura)           misura "${2:-25}" ;;
stato)            stato ;;
registro)         registro "${2:-60}" ;;
spegni)           spegni ;;
tutto)            certifica && porte ;;
*)                sed -n '2,30p' "$0"; exit 2 ;;
esac
