#!/bin/bash
#
# 01-b2-sni-ngtcp2.sh — costruisce il server d'esempio di ngtcp2, che e' il
#                       bersaglio della prova SNI.
#
#   bash 01-b2-sni-ngtcp2.sh            costruisce
#   bash 01-b2-sni-ngtcp2.sh controlla  dice solo che cosa c'e'
#
# ---------------------------------------------------------------------------
# PERCHE' ESISTE, E PERCHE' VIENE PRIMA DI QUALUNQUE RIGA DI COLLANTE
#
# ⛔ Il 9 agosto 2026 `lsquic` e' stata eliminata DOPO 333 righe di collante,
#    per una ragione che nessuno aveva previsto: in modalita' HTTP/3 pretende
#    l'SNI per trovare il certificato, e chi si collega a un INDIRIZZO IP non
#    lo manda — che e' il caso primario del prodotto (`SPECIFICHE.md`, §1.7).
#
# ⭐ Da li' il criterio nuovo di `DECISIONI.md` §6.4: la libreria DEVE servire
#    un certificato senza SNI, e la cosa si prova PER PRIMA su ogni candidata.
#    Costa una connessione.  Provarla dopo il collante costa il collante.
#
# Questo script non prova niente: PREPARA il bersaglio.  La misura la fa
# `01-b2-sonda-sni.py`, che e' l'altra meta' del banco.
#
# ---------------------------------------------------------------------------
# PERCHE' IL LORO ESEMPIO E NON UN SERVER NOSTRO
#
# Un server nostro sarebbe collante — cioe' esattamente la cosa che questa
# prova deve venire PRIMA di scrivere.  `ngtcp2/examples/bsslserver` e' il
# punto di partenza di chiunque usi questa libreria con BoringSSL, ed e' gia'
# scritto.  Se il certificato non si serve nemmeno da li', non si serve.
#
# ⚠ E il numero di righe di quell'esempio e' un dato di B2, non un dettaglio:
#   e' la colonna «quanto collante resta a noi» di §6.4.  Lo script lo conta.
#
# ---------------------------------------------------------------------------
# L'ATTESO, DICHIARATO PRIMA (regola B0.4)
#
#   1. libev presente                                   -> atteso: da installare
#   2. nghttp3 installato in un prefisso                -> atteso: si'
#   3. cmake TROVA libev e libnghttp3                   -> atteso: si'
#   4. ⛔ il binario `bsslserver` ESISTE                 -> atteso: si'
#
# ⛔ Il punto 4 e' il controllo che rende credibili i primi tre, ed e' la
#    lezione del 9 agosto ripetuta in un'altra forma: `examples/CMakeLists.txt`
#    riga 179 costruisce `bsslserver` solo `if(LIBEV_FOUND AND HAVE_BORINGSSL
#    AND LIBNGHTTP3_FOUND)` [R].  Se una delle tre manca, cmake NON si lamenta:
#    salta il blocco IN SILENZIO e la costruzione riesce.  Un «ninja: build
#    stopped: nothing to do» e nessun server.  Quindi non si guarda l'uscita di
#    ninja: si guarda se il file c'e'.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
BSSL="$SRC/boringssl"
PREFISSO="$SRC/prefisso"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-costruisci}
SERVER="$SRC/ngtcp2/build/examples/bsslserver"

log "Stato di partenza"
inf "sorgenti  $SRC"
for f in "$BSSL/build/libssl.a" "$SRC/nghttp3/build/lib/libnghttp3.a" "$SRC/ngtcp2/build/lib/libngtcp2.a"; do
	[ -f "$f" ] && inf "c'e'    $f" || { ko "manca  $f — lancia prima 01-b2-costruisci.sh e 01-b2-costruisci-ngtcp2.sh"; exit 2; }
done
[ -f "$SERVER" ] && inf "bsslserver: gia' costruito" || inf "bsslserver: da costruire"

if [ "$AZIONE" = controlla ]; then
	[ -f "$SERVER" ] && exit 0 || exit 1
fi

# ---------------------------------------------------------------------------
# 1. libev — la dipendenza che manca, e che NON si installa a mano
# ---------------------------------------------------------------------------
log "libev"
if [ -f /usr/include/ev.h ]; then
	ok "ev.h presente"
else
	inf "assente: la installo adesso, ma il posto dove deve stare e'"
	inf "v1/banco/provision.sh — dove e' gia' stata aggiunta (LEZIONI.md §2.5-bis:"
	inf "una dipendenza installata a mano diventa invisibile in un giorno)"
	# ⚠ Niente `2>/dev/null`: se apt fallisce si deve vedere il perche'.
	apt-get install -y --no-install-recommends libev-dev
	if [ ! -f /usr/include/ev.h ]; then
		ko "ev.h ancora assente dopo l'installazione"
		exit 3
	fi
	ok "ev.h installato"
fi

# ---------------------------------------------------------------------------
# 2. nghttp3 in un prefisso
#
# ⚠ Non e' pignoleria: `cmake/FindLibnghttp3.cmake` legge la versione da
#   `<include>/nghttp3/version.h` e la confronta con il 1.18.0 preteso dal
#   CMakeLists principale [R].  Nell'albero dei sorgenti `nghttp3.h` sta in
#   `lib/includes` e `version.h` in `build/lib/includes`: due cartelle diverse,
#   e nessuna delle due contiene tutt'e due i file.  Puntare cmake all'albero
#   fallisce la ricerca in silenzio.  L'installazione le mette insieme.
# ---------------------------------------------------------------------------
log "nghttp3 installato in $PREFISSO"
if [ ! -f "$PREFISSO/include/nghttp3/nghttp3.h" ]; then
	cmake --install "$SRC/nghttp3/build" --prefix "$PREFISSO" || { ko "installazione fallita"; exit 4; }
fi
for f in "$PREFISSO/include/nghttp3/nghttp3.h" "$PREFISSO/include/nghttp3/version.h"; do
	[ -f "$f" ] && ok "c'e' $f" || { ko "manca $f"; exit 4; }
done
VERS=$(grep -h 'define NGHTTP3_VERSION ' "$PREFISSO/include/nghttp3/version.h" | head -1)
inf "$VERS   (il CMakeLists di ngtcp2 ne pretende >= 1.18.0)"

# ---------------------------------------------------------------------------
# 3. ngtcp2, riconfigurato perche' trovi le due dipendenze degli esempi
# ---------------------------------------------------------------------------
log "ngtcp2, riconfigurato con libev e libnghttp3"
export PKG_CONFIG_PATH="$PREFISSO/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
# ⛔ ENABLE_SHARED_LIB=ON, e non e' un ripensamento estetico.  `[M]` 10 agosto
#    2026: con la libreria SOLO statica gli esempi non si collegano —
#
#        /usr/bin/ld: cannot find -lngtcp2
#
#    perche' il CMakeLists degli esempi chiede il bersaglio `ngtcp2` [R], che
#    esiste solo se la condivisa e' accesa; senza, cmake non protesta e
#    degrada il nome a una libreria di sistema che non c'e'.  ⚠ Il prodotto
#    la vorra' statica: questa riga vale per il BANCO, e la differenza sta
#    scritta qui perche' non venga ereditata per distrazione.
CONF=$(cmake -B "$SRC/ngtcp2/build" -S "$SRC/ngtcp2" -GNinja \
	-DCMAKE_BUILD_TYPE=Release \
	-DENABLE_STATIC_LIB=ON -DENABLE_SHARED_LIB=ON \
	-DENABLE_BORINGSSL=ON \
	-DBORINGSSL_INCLUDE_DIR="$BSSL/include" \
	-DBORINGSSL_LIBRARIES="$BSSL/build/libssl.a;$BSSL/build/libcrypto.a" \
	-DLIBNGHTTP3_INCLUDE_DIR="$PREFISSO/include" \
	-DLIBNGHTTP3_LIBRARY="$PREFISSO/lib/libnghttp3.a" 2>&1)
STATO=$?
printf '%s\n' "$CONF" | sed 's/^/        /'
if [ "$STATO" -ne 0 ]; then
	ko "cmake fallito"
	exit 5
fi

# ⛔ Il riepilogo di cmake DICE se ha trovato le due dipendenze, ed e' quel che
#    separa «gli esempi non si costruiscono» da «gli esempi non si costruiranno
#    e nessuno l'ha detto».  Si legge, non si spera.
for chiave in Libev Libnghttp3 Boringssl; do
	RIGA=$(printf '%s\n' "$CONF" | grep -i "^ *$chiave:" | head -1)
	if [ -n "$RIGA" ]; then
		inf "riepilogo cmake ->$RIGA"
	else
		inf "riepilogo cmake -> nessuna riga per '$chiave'"
	fi
done

log "Compilazione"
ninja -C "$SRC/ngtcp2/build" bsslserver bsslclient
STATO=$?
inf "ninja e' uscito con $STATO"

# ---------------------------------------------------------------------------
# 4. ⛔ IL CONTROLLO CHE CONTA: il binario esiste?
# ---------------------------------------------------------------------------
log "Esito"
# ⛔ Due modi di non avere il binario, e vanno DISTINTI: se li si confonde, la
#    diagnosi manda a cercare nel posto sbagliato.  Il primo giro del 10 agosto
#    2026 ha stampato «cmake ha saltato gli esempi in silenzio» per un errore
#    di COLLEGAMENTO, che e' l'opposto — cmake li aveva configurati benissimo.
if [ ! -f "$SERVER" ] && [ "$STATO" -ne 0 ]; then
	ko "⛔ la compilazione e' fallita (ninja: $STATO): l'errore e' qui sopra"
	ko "   NON e' un problema di configurazione — cmake aveva trovato tutto"
	exit 6
fi
if [ ! -f "$SERVER" ]; then
	ko "⛔ ninja e' uscito con 0 e $SERVER NON esiste"
	ko "   cmake ha saltato il blocco degli esempi in silenzio: guarda il"
	ko "   riepilogo qui sopra e vedi quale delle tre condizioni e' falsa"
	exit 6
fi
ok "bsslserver costruito"
inf "$(ls -la "$SERVER" | sed 's/  */ /g')"

# ⚠ La condivisa non e' in un percorso di sistema: chi lancia il server deve
#   dire dov'e'.  Lo si dichiara qui, e lo si PROVA subito col --help — cosi'
#   «compilato» e «eseguibile» restano due cose distinte invece di scoprirlo
#   in mezzo a una misura.
export LD_LIBRARY_PATH="$SRC/ngtcp2/build/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
inf "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
AIUTO=$("$SERVER" --help 2>&1 | head -3)
if [ -n "$AIUTO" ]; then
	ok "risponde a --help:"
	printf '%s\n' "$AIUTO" | sed 's/^/        /'
else
	ko "non risponde a --help: compilato ma non eseguibile"
	exit 6
fi

# ⚠ Il conto delle righe dell'esempio: e' la colonna «quanto collante» di §6.4,
#   e va misurato invece che stimato.  Si dichiara che cosa si e' contato.
log "Quanto pesa il loro esempio — il dato di §6.4"
# ⚠ L'elenco NON e' a memoria: e' quello che ninja ha davvero collegato in
#   `examples/bsslserver`, letto dalla riga di collegamento.  Il primo giro
#   nominava `tls_session_base_boringssl.cc`, che non esiste — si chiama
#   `..._quictls.cc` — e il banco l'ha detto invece di contare 10 file
#   fingendo che fossero 11.
FONTI=(server.cc server_base.cc http3_server_proto_codec.cc http.cc util.cc
       util_openssl.cc shared.cc siphash.cc debug.cc
       tls_server_context_boringssl.cc tls_server_session_boringssl.cc
       tls_session_base_quictls.cc tls_shared_boringssl.cc)
TOT=0
MANCANTI=0
for f in "${FONTI[@]}"; do
	P="$SRC/ngtcp2/examples/$f"
	if [ -f "$P" ]; then
		N=$(wc -l < "$P")
		TOT=$((TOT + N))
	else
		MANCANTI=$((MANCANTI + 1))
		inf "⚠ non trovato: $f  (il conto e' incompleto)"
	fi
done
inf "${#FONTI[@]} file elencati, $MANCANTI non trovati"
inf "righe del server d'esempio (solo .cc, senza le intestazioni): $TOT"
inf "⚠ e' il loro HTTP/3 completo, non il minimo — serve da tetto, non da stima"

printf '\n'
ok "il bersaglio e' pronto: adesso la misura, con 01-b2-sonda-sni.py"
exit 0
