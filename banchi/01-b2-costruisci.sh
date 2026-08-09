#!/bin/bash
#
# 01-b2-costruisci.sh — costruisce le candidate del banco B2 della fase 1.
#
#   bash 01-b2-costruisci.sh lsquic     BoringSSL + lsquic con WebTransport
#   bash 01-b2-costruisci.sh controlla  dice solo che cosa c'e' gia'
#
# ---------------------------------------------------------------------------
# CHE COSA DECIDE, E PERCHE' NON BASTA LEGGERE
#
# `DECISIONI.md` §6.4 sceglie la libreria QUIC, e il criterio e' cambiato il 9
# agosto 2026: non basta che parli QUIC, deve portare HTTP/3 e WebTransport
# LATO SERVER.  Il censimento del 9 notte ha letto le quattro candidate e ha
# stabilito che:
#
#   - `quiche` e `ngtcp2+nghttp3` danno le FONDAMENTA (extended CONNECT,
#     datagram, capsule) e non lo strato WebTransport;
#   - `lsquic` ha `OPTION(LSQUIC_WEBTRANSPORT ... OFF)` nel CMakeLists [R],
#     ⛔ ma nell'intestazione pubblica espone SOLO due impostazioni e quattro
#     funzioni di classificazione degli stream — nessuna API di sessione,
#     nessuna apertura di stream WT, nessun datagram WT.
#
# ⛔ E' esattamente E1 — necessario preso per sufficiente.  Un flag di
#    compilazione che si chiama WEBTRANSPORT_SERVER_SUPPORT non dice che il
#    server faccia WebTransport: dice che qualcuno ha scritto del codice dietro
#    quel nome.  Quanto ne faccia si MISURA, e questo script prepara la misura.
#
# ⚠ E un dettaglio che vale come indizio, non come prova: il commento di
#   `es_webtransport_server` nell'intestazione dice «Enable datagram extension
#   for http3 server» — cioe' documenta un'ALTRA cosa.  Un campo la cui
#   documentazione parla di qualcos'altro e' un campo che nessuno ha riletto.
#
# ---------------------------------------------------------------------------
# L'ATTESO, DICHIARATO PRIMA (regola B0.4 di `fasi/01-filo-nudo.md`)
#
#   1. BoringSSL compila                                   -> atteso: si'
#   2. lsquic compila CON -DLSQUIC_WEBTRANSPORT=ON          -> atteso: si'
#   3. i quattro simboli WT sono nella libreria prodotta    -> atteso: 4 su 4
#
# ⛔ Il punto 3 e' il controllo che rende credibili i primi due: una libreria
#    che compila «con il flag» e non contiene i simboli e' una libreria in cui
#    il flag non ha fatto niente — e il primo a scoprirlo sarebbe stato chi
#    scrive il server, tre giorni dopo.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
# ⚠ Nessun `-b <ramo>`: si prende il ramo predefinito del deposito.  Il primo
#   giro del 9 agosto 2026 chiedeva `master` a BoringSSL e falliva con «Remote
#   branch master not found» — Google l'ha rinominato.  Un ramo scritto a mano
#   in uno script e' una dipendenza dal nome di qualcun altro.
#
# ⛔ E il fallimento e' arrivato con «uscita 0» sul terminale di chi guardava,
#    perche' il comando remoto era in pipe con `tail`: lo stato d'uscita era
#    quello di `tail`.  E' `LEZIONI.md` §1.9 — zero e fallimento con la stessa
#    faccia — presa nell'INVOCAZIONE invece che nello script.  Chi lancia
#    questo banco non ci metta un `| tail` davanti senza `PIPESTATUS`.

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-lsquic}

mkdir -p "$SRC" || exit 2
cd "$SRC" || exit 2

# ---------------------------------------------------------------------------
# 0. Che cosa c'e' gia'
# ---------------------------------------------------------------------------
log "Stato di partenza"
inf "go       $(go version 2>/dev/null || echo MANCA)"
inf "cmake    $(cmake --version 2>/dev/null | head -1 || echo MANCA)"
inf "gcc      $(gcc -dumpversion 2>/dev/null || echo MANCA)"
inf "sorgenti $SRC"
[ -d "$SRC/boringssl" ] && inf "boringssl gia' clonato" || inf "boringssl da clonare"
[ -d "$SRC/lsquic" ]    && inf "lsquic gia' clonato"    || inf "lsquic da clonare"

if [ "$AZIONE" = controlla ]; then
	exit 0
fi

# ---------------------------------------------------------------------------
# 1. BoringSSL
#
# ⚠ lsquic non parla con OpenSSL: vuole BoringSSL, e BoringSSL si compila con
#   Go.  E' la ragione per cui `golang-go` e' entrato in `provision.sh`.
# ---------------------------------------------------------------------------
log "BoringSSL"
if [ ! -d "$SRC/boringssl" ]; then
	git clone --depth 1 https://boringssl.googlesource.com/boringssl "$SRC/boringssl" \
		|| { ko "clone fallito"; exit 3; }
fi
if [ ! -f "$SRC/boringssl/build/libssl.a" ] && [ ! -f "$SRC/boringssl/build/ssl/libssl.a" ]; then
	cmake -B "$SRC/boringssl/build" -S "$SRC/boringssl" -GNinja -DCMAKE_BUILD_TYPE=Release \
		|| { ko "cmake fallito"; exit 3; }
	ninja -C "$SRC/boringssl/build" ssl crypto || { ko "compilazione fallita"; exit 3; }
fi
BSSL_SSL=$(find "$SRC/boringssl/build" -name libssl.a | head -1)
BSSL_CRY=$(find "$SRC/boringssl/build" -name libcrypto.a | head -1)
if [ -n "$BSSL_SSL" ] && [ -n "$BSSL_CRY" ]; then
	ok "libssl.a e libcrypto.a costruite"
else
	ko "le librerie di BoringSSL non ci sono"
	exit 3
fi

# ---------------------------------------------------------------------------
# 2. lsquic, CON il flag
# ---------------------------------------------------------------------------
log "lsquic con LSQUIC_WEBTRANSPORT=ON"
if [ ! -d "$SRC/lsquic" ]; then
	git clone --depth 1 --recursive https://github.com/litespeedtech/lsquic "$SRC/lsquic" \
		|| { ko "clone fallito"; exit 4; }
fi
inf "versione $(cd "$SRC/lsquic" && git describe --tags 2>/dev/null || echo '(senza tag)')"

cmake -B "$SRC/lsquic/build" -S "$SRC/lsquic" -GNinja \
	-DCMAKE_BUILD_TYPE=Release \
	-DLSQUIC_WEBTRANSPORT=ON \
	-DBORINGSSL_DIR="$SRC/boringssl" \
	-DBORINGSSL_LIB_ssl="$BSSL_SSL" \
	-DBORINGSSL_LIB_crypto="$BSSL_CRY" \
	-DBORINGSSL_INCLUDE="$SRC/boringssl/include" \
	-DLSQUIC_TESTS=OFF \
	|| { ko "cmake fallito"; exit 4; }
ninja -C "$SRC/lsquic/build" lsquic || { ko "compilazione fallita"; exit 4; }
LIB=$(find "$SRC/lsquic/build" -name 'liblsquic.a' | head -1)
[ -n "$LIB" ] && ok "liblsquic.a costruita" || { ko "liblsquic.a non trovata"; exit 4; }

# ---------------------------------------------------------------------------
# 3. ⛔ IL CONTROLLO: il flag ha prodotto qualcosa?
#
# Non «compila», non «il flag e' accettato»: i SIMBOLI.  Un flag ignorato
# produce una libreria identica a quella senza flag, e nessun messaggio.
# ---------------------------------------------------------------------------
log "Il controllo: i simboli WebTransport dentro la libreria"
# ⛔ Il banco dichiara SU CHE COSA sta guardando, e quanti ne vede in tutto,
#    prima di dire quali mancano.  Il primo giro del 9 agosto 2026 ha detto
#    «0 su 4» mentre una lettura a mano sullo stesso archivio ne mostrava 4:
#    senza queste tre righe non c'era modo di sapere chi dei due mentiva.
inf "archivio $LIB"
inf "byte     $(stat -c %s "$LIB" 2>/dev/null || echo '?')"
inf "simboli che nominano webtransport, a occhio: $(nm -g --defined-only "$LIB" 2>/dev/null | grep -ci webtransport)"
nm -g --defined-only "$LIB" 2>/dev/null | grep -i webtransport | sed 's/^/        /' | head -8
ATTESI=(
	lsquic_stream_set_webtransport_session
	lsquic_stream_is_webtransport_session
	lsquic_stream_is_webtransport_client_bidi_stream
	lsquic_stream_get_webtransport_session_stream_id
)
# ⛔ I simboli si leggono UNA volta e si cercano in una stringa, non in un tubo.
#
#    Il primo giro del 9 agosto 2026 faceva `nm ... | grep -q " $s$"` e diceva
#    **0 su 4** mentre i quattro simboli erano nell'archivio — li stampava lui
#    stesso tre righe sopra.  La causa: `set -o pipefail` in cima, e `grep -q`
#    che esce al PRIMO riscontro chiudendo il tubo.  `nm` sta ancora scrivendo,
#    prende SIGPIPE, muore con 141 — e `pipefail` fa valere quel 141 come esito
#    della pipeline.  ⛔ **Il riscontro riuscito veniva letto come fallimento**:
#    piu' il simbolo era facile da trovare, prima grep usciva, piu' sicuro era
#    il falso rosso.
#
#    E' `LEZIONI.md` §2.3 — una prova che boccia il codice giusto costa quanto
#    una che promuove quello sbagliato — nella stessa famiglia del banco della
#    rotella.  Qui avrebbe cancellato la candidata migliore di `DECISIONI.md`
#    §6.4 con un [M] falso contro un [R].
SIMBOLI=$(nm -g --defined-only "$LIB" 2>/dev/null)
TROVATI=0
for s in "${ATTESI[@]}"; do
	if grep -q " $s\$" <<<"$SIMBOLI"; then
		ok "$s"
		TROVATI=$((TROVATI + 1))
	else
		ko "$s  — assente"
	fi
done

printf '\n'
log "Esito"
inf "atteso:    4 simboli su 4"
inf "trovati:   $TROVATI su 4"
if [ "$TROVATI" -eq 4 ]; then
	ok "il flag ha prodotto codice: si puo' passare alla sessione vera"
	exit 0
else
	ko "il flag NON ha prodotto quel che dichiara"
	printf '\n    ⛔ E questo e\047 il caso in cui il banco vale piu\047 di tutto:\n'
	printf '       la libreria compila, il flag e\047 accettato, e il codice non c\047e\047.\n'
	exit 1
fi
