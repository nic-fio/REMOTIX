#!/bin/bash
#
# costruisci-in-contenitore.sh — ⭐ LA RISPOSTA ALLA DOMANDA «COME SI COSTRUISCE»
#
#   bash src/costruisci-in-contenitore.sh              costruisce `src/remotix`
#   bash src/costruisci-in-contenitore.sh dipendenze   dice solo che cosa c'e'
#   bash src/costruisci-in-contenitore.sh pulisci      butta gli oggetti
#   bash src/costruisci-in-contenitore.sh <altro>      lo passa a `make`
#
# ---------------------------------------------------------------------------
# ⛔ IL BLOCCO CHE QUESTO FILE SCIOGLIE, e la data
#
# `fasi/rapporti/F4-IN-12-mandato-prossima-sessione.md` §3, 14 agosto 2026:
# *«Non sono riuscito a costruire il C.  E finche' non si costruisce, ogni riga
# nuova e' codice che nessuno ha mai visto girare.  ⇒ La prima domanda alla
# prossima sessione e' all'utente: come si costruisce questo progetto?»*
#
# ⭐ La risposta non ha avuto bisogno dell'utente, e non e' `/media/REMOTIX`:
#    **`podman` da utente, l'albero montato dentro, il binario che esce qui.**
#    Nessun `sudo` sull'host — root si e' soltanto **dentro** il contenitore,
#    che e' l'unico posto in cui `apt` serve.
#
# ⛔ E il contenitore NON e' quello della macchina di prova: quello ha `gcc` ma
#    non vede `/media/REMOTIX`, e il `/srv/src` che mostra non e' quello
#    dell'host — le tre strade morte sono elencate in `src/Contenitore`.
#
# ---------------------------------------------------------------------------
# ⚠ IL MONTAGGIO E' L'ALBERO INTERO, non `src/`, e la ragione e' il `Makefile`:
#   il bersaglio `impronte` confronta `src/rcp.c` con `../banchi/rcp/rcp.c` e
#   RIFIUTA di compilare se non lo trova (rilievo R12.3).  ⛔ Montando solo
#   `src/` la copia gemella sparirebbe, e il `Makefile` direbbe — giustamente —
#   «non ho potuto guardare».
#
# ⚠ `:Z` NON si usa: su questa macchina SELinux non etichetta, e `:Z`
#   riscriverebbe le etichette dell'albero dei sorgenti dell'utente.
set -uo pipefail

ALBERO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
IMMAGINE=${IMMAGINE:-localhost/remotix-costruzione}
AZIONE=${1:-tutto}

if ! command -v podman >/dev/null 2>&1; then
	printf '⛔ podman non c%s: e il contenitore e l unica strada che costruisce.\n' "'e'"
	exit 2
fi

# ⛔ L'immagine si CONTROLLA, e la sua assenza non e' un guasto da indovinare:
#    e' una riga che dice il comando da battere.
if ! podman image exists "$IMMAGINE"; then
	printf '⛔ l immagine «%s» non c e ancora.  Si costruisce una volta sola:\n\n' "$IMMAGINE"
	printf '    podman build -t remotix-costruzione -f %s/src/Contenitore %s/src\n\n' \
	       "$ALBERO" "$ALBERO"
	printf '   (~4 minuti: ci dentro si costruiscono nghttp3 e ngtcp2 dai sorgenti,\n'
	printf '    perche% i pacchetti di Debian sono 1.8 e 1.11 e il ponte\n' "'"
	printf '    ngtcp2_crypto_ossl nei pacchetti NON C E affatto.)\n'
	exit 3
fi

# ⛔ `--userns=keep-id`: i file che escono devono essere DELL'UTENTE, non di un
#    uid rimappato.  Senza, `src/remotix` nasce di proprieta' di un utente che
#    sull'host non esiste, e il `git status` successivo mostra un albero che non
#    si puo' piu' toccare senza `sudo` — cioe' il blocco di stanotte, spostato.
printf '== costruzione dentro «%s» — albero %s\n' "$IMMAGINE" "$ALBERO"
podman run --rm \
	--userns=keep-id \
	-v "$ALBERO:/albero" \
	-w /albero/src \
	"$IMMAGINE" \
	make "$AZIONE"
uscita=$?

if [ $uscita -eq 0 ] && [ "$AZIONE" = tutto ]; then
	if [ -x "$ALBERO/src/remotix" ]; then
		printf '\n⭐ costruito: %s\n' "$ALBERO/src/remotix"
		ls -l "$ALBERO/src/remotix"
	fi

	# ⛔⛔⭐ E IL BANCO DI `rcp.c` GIRA QUI, a ogni costruzione — 16 agosto 2026.
	#
	#   `[M]` `banchi/04-b31-tela.c` — 19 casi, il banco piu' forte che abbiamo
	#   sul modulo piu' delicato — e' rimasto **11 su 18, rosso, per un giorno
	#   intero** senza che nessuno se ne accorgesse.  Non perche' fosse difficile
	#   da lanciare: perche' **nessuno lo lanciava**.
	#
	# ⚠ E la cura NON e' un lanciatore: di banchi che si giudicano da soli e
	#   girano senza macchina ce n'e' UNO, e uno script per lanciarne uno e'
	#   burocrazia con un altro nome — parole dell'utente, «se i punti non
	#   toccano il prodotto e' solo rumore burocratico».
	#
	# ⇒ La cura e' che giri DA SE', dove si passa comunque: due secondi, e chi
	#   compila non deve ricordarsi niente.  ⛔ E non ferma la costruzione: il
	#   binario c'e' e puo' servire — ma il rosso si vede, ed e' l'unica cosa
	#   che serviva.
	if command -v gcc >/dev/null 2>&1 \
	   && [ -f "$ALBERO/banchi/04-b31-tela.c" ] && [ -f "$ALBERO/src/rcp.c" ]; then
		B=$(mktemp -u /tmp/04-b31.XXXXXX)
		if gcc -O1 -std=gnu11 -w -D_GNU_SOURCE -o "$B" \
		       "$ALBERO/banchi/04-b31-tela.c" "$ALBERO/src/rcp.c" 2>/dev/null; then
			if RIGA=$("$B" 2>&1 | grep -a passati); then
				case "$RIGA" in
				*"falliti 0"*) printf '⭐ 04-b31 (la tela, %s):%s\n' \
				                      "$(echo "$RIGA" | tr -s ' ')" '' ;;
				*)             printf '\n⛔ 04-b31 E ROSSO:%s\n' "$RIGA"
				               printf '   lo rilanci con:  gcc -O1 -std=gnu11 -w -D_GNU_SOURCE \\\n'
				               printf '        -o /tmp/b31 banchi/04-b31-tela.c src/rcp.c && /tmp/b31\n' ;;
				esac
			fi
			rm -f "$B"
		fi
	fi
fi
exit $uscita
