#!/bin/bash
#
# 01-b2-costruisci-ngtcp2.sh — la seconda candidata di B2.
#
#   bash 01-b2-costruisci-ngtcp2.sh          costruisce
#   bash 01-b2-costruisci-ngtcp2.sh controlla dice solo che cosa c'e'
#
# ---------------------------------------------------------------------------
# PERCHE' DAL LORO ESEMPIO E NON DAL FOGLIO BIANCO
#
# B2 deve misurare **quanto collante resta a noi**, e quel numero ha senso solo
# se si parte da dove parte chiunque: il server d'esempio del progetto.
# Scrivere tutto da zero misurerebbe la nostra pazienza, non la libreria.
#
# ⚠ E su ngtcp2 non esiste un «server minimo da cinquanta righe»: la libreria
#   e' deliberatamente di basso livello — socket UDP, TLS montato a mano,
#   connection ID, timer di ritrasmissione — e sopra ci va nghttp3 per
#   l'HTTP/3.  Questo e' un dato di B2, non una lamentela: e' esattamente la
#   colonna «quanto collante» di `DECISIONI.md` §6.4.
#
# ---------------------------------------------------------------------------
# L'ATTESO, DICHIARATO PRIMA (regola B0.4)
#
#   1. nghttp3 compila                                     -> atteso: si'
#   2. ngtcp2 compila con BoringSSL                        -> atteso: si'
#   3. il server d'esempio si costruisce                   -> atteso: si'
#   4. ⛔ il loro esempio parla gia' WebTransport?          -> atteso: NO
#
# ⛔ Il punto 4 e' quello che conta, ed e' scritto come previsione: nghttp3
#    implementa RFC 9220 (l'extended CONNECT di HTTP/3) `[S]`, cioe' la
#    FONDAMENTA, e non lo strato WebTransport.  Se l'esempio lo parlasse gia',
#    la previsione e' sbagliata e va scritto perche' — che e' `LEZIONI.md`
#    §1.11 applicata a una lettura invece che a una misura.
#
# ⚠ E si riusa BoringSSL gia' costruito da `01-b2-costruisci.sh`: due pile TLS
#   diverse per due candidate darebbero due misure non confrontabili, che e'
#   la ragione per cui `provision-server.sh` e `provision-vm.sh` hanno lo
#   stesso elenco.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
BSSL="$SRC/boringssl"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-costruisci}

log "Stato di partenza"
inf "sorgenti  $SRC"
for d in boringssl nghttp3 ngtcp2; do
	[ -d "$SRC/$d" ] && inf "$d: clonato" || inf "$d: da clonare"
done
if [ ! -f "$BSSL/build/libssl.a" ]; then
	ko "BoringSSL non e' costruito: lancia prima 01-b2-costruisci.sh"
	exit 2
fi
ok "BoringSSL riusato da lsquic (stessa pila TLS per tutte le candidate)"

[ "$AZIONE" = controlla ] && exit 0

# ---------------------------------------------------------------------------
# 1. nghttp3 — l'HTTP/3, cioe' la meta' che porta l'extended CONNECT
# ---------------------------------------------------------------------------
log "nghttp3"
if [ ! -d "$SRC/nghttp3" ]; then
	git clone --depth 1 --recursive https://github.com/ngtcp2/nghttp3 "$SRC/nghttp3" \
		|| { ko "clone fallito"; exit 3; }
fi
if [ ! -f "$SRC/nghttp3/build/lib/libnghttp3.a" ]; then
	cmake -B "$SRC/nghttp3/build" -S "$SRC/nghttp3" -GNinja \
		-DCMAKE_BUILD_TYPE=Release -DENABLE_LIB_ONLY=ON -DENABLE_STATIC_LIB=ON \
		|| { ko "cmake fallito"; exit 3; }
	ninja -C "$SRC/nghttp3/build" || { ko "compilazione fallita"; exit 3; }
fi
NGH=$(find "$SRC/nghttp3/build" -name 'libnghttp3.a' | head -1)
[ -n "$NGH" ] && ok "libnghttp3.a costruita" || { ko "libnghttp3.a assente"; exit 3; }
inf "versione $(cd "$SRC/nghttp3" && git describe --tags 2>/dev/null || echo '(senza tag)')"

# ---------------------------------------------------------------------------
# 2. ngtcp2 — il QUIC
# ---------------------------------------------------------------------------
log "ngtcp2 con BoringSSL"
if [ ! -d "$SRC/ngtcp2" ]; then
	git clone --depth 1 --recursive https://github.com/ngtcp2/ngtcp2 "$SRC/ngtcp2" \
		|| { ko "clone fallito"; exit 4; }
fi
inf "versione $(cd "$SRC/ngtcp2" && git describe --tags 2>/dev/null || echo '(senza tag)')"

if [ ! -f "$SRC/ngtcp2/build/lib/libngtcp2.a" ]; then
	cmake -B "$SRC/ngtcp2/build" -S "$SRC/ngtcp2" -GNinja \
		-DCMAKE_BUILD_TYPE=Release \
		-DENABLE_STATIC_LIB=ON -DENABLE_SHARED_LIB=OFF \
		-DENABLE_BORINGSSL=ON \
		-DBORINGSSL_INCLUDE_DIR="$BSSL/include" \
		-DBORINGSSL_LIBRARIES="$BSSL/build/libssl.a;$BSSL/build/libcrypto.a" \
		|| { ko "cmake fallito"; exit 4; }
	ninja -C "$SRC/ngtcp2/build" || { ko "compilazione fallita"; exit 4; }
fi
NGT=$(find "$SRC/ngtcp2/build" -name 'libngtcp2.a' | head -1)
[ -n "$NGT" ] && ok "libngtcp2.a costruita" || { ko "libngtcp2.a assente"; exit 4; }

# ---------------------------------------------------------------------------
# 3. ⛔ IL CONTROLLO CHE CONTA: il loro esempio parla WebTransport?
#
# Non «compila»: che cosa sa fare.  Si cercano le tre cose senza le quali una
# sessione WebTransport non nasce, e si dice quante se ne trovano.
# ---------------------------------------------------------------------------
log "Il controllo: quanto WebTransport c'e' gia'"
inf "atteso: NESSUNO — nghttp3 porta l'extended CONNECT (RFC 9220), non lo strato WT"

# ⛔ TRE DIFETTI IN NOVE RIGHE, IL 9 AGOSTO 2026, E TUTTI DELLA STESSA
#    FAMIGLIA: il banco diceva ZERO dove non aveva GUARDATO.
#
#    1. i due alberi erano passati come UNA stringa — `"$SRC/ngtcp2 $SRC/nghttp3"`
#       — quindi grep riceveva un percorso solo, con uno spazio dentro, che non
#       esiste.  Zero risultati;
#    2. `2>/dev/null` nascondeva il «No such file or directory» che l'avrebbe
#       detto subito.  ⛔ E' precisamente cio' che `REVIEWER.md` §1 punto 4
#       ordina di rifiutare;
#    3. il `printf` diagnostico finiva dentro `$(...)`, quindi spariva dal
#       terminale: il banco non mostrava nemmeno che cosa stesse cercando.
#
#    Risultato: «nessuna traccia di SETTINGS_WT_MAX_SESSIONS: la previsione
#    regge» — un VERDE stampato da una ricerca mai eseguita.
#
# ⭐ La cura non e' aggiustare il grep: e' che il banco DICA SU CHE COSA HA
#    GUARDATO.  Un conteggio senza il suo denominatore non e' una misura.
ALBERI=("$SRC/ngtcp2" "$SRC/nghttp3")
for a in "${ALBERI[@]}"; do
	if [ ! -d "$a" ]; then
		ko "l'albero $a non esiste: la ricerca non si puo' fare"
		exit 5
	fi
done
FILE_TOT=$(find "${ALBERI[@]}" \( -name '*.c' -o -name '*.h' -o -name '*.cc' -o -name '*.hh' \) | wc -l)
inf "si guarda dentro $FILE_TOT file di ${#ALBERI[@]} alberi"
if [ "$FILE_TOT" -lt 100 ]; then
	ko "solo $FILE_TOT file: la ricerca sta guardando nel posto sbagliato"
	exit 5
fi

cerca()
{
	local etichetta=$1 modello=$2
	local n
	# ⚠ Niente `2>/dev/null`: se grep si lamenta, si deve vedere.
	n=$(grep -rIl --include='*.c' --include='*.h' --include='*.cc' --include='*.hh' \
		-e "$modello" "${ALBERI[@]}" | wc -l)
	printf '    --  %-34s %s file\n' "$etichetta" "$n" >&2
	echo "$n"
}

N1=$(cerca "SETTINGS_WT_MAX_SESSIONS (0xc671706a)" "c671706a")
N2=$(cerca "il token 'webtransport'"               "webtransport")
N3=$(cerca "l'extended CONNECT (:protocol)"        "ENABLE_CONNECT_PROTOCOL\|:protocol")

# ⛔ E IL CONTROLLO POSITIVO DELLA RICERCA STESSA: si cerca una cosa che DEVE
#    esserci.  Se anche questa da' zero, non e' la libreria a mancare: e' il
#    grep che non sta leggendo niente, ed e' l'errore che questo riquadro
#    racconta.
CTRL=$(cerca "controllo: la parola 'nghttp3'"      "nghttp3")
if [ "$CTRL" -eq 0 ]; then
	ko "⛔ il controllo positivo della ricerca e' FALLITO: zero file nominano 'nghttp3'"
	ko "   la ricerca non sta guardando niente. Nessun numero qui sotto vale."
	exit 5
fi
ok "controllo positivo della ricerca: 'nghttp3' trovato in $CTRL file"

printf '\n'
log "Esito"
if [ "$N1" -eq 0 ]; then
	ok "nessuna traccia di SETTINGS_WT_MAX_SESSIONS: la previsione regge"
	inf "⇒ lo strato WebTransport lo scriviamo noi, e le righe si CONTANO"
else
	ko "⛔ la previsione e' SBAGLIATA: SETTINGS_WT_MAX_SESSIONS c'e' in $N1 file"
	inf "va riletto perche', prima di scrivere una riga di collante"
fi
inf "extended CONNECT presente in $N3 file — e' la fondamenta, non lo strato"
exit 0
