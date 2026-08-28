#!/bin/bash
#
# 01-b2-sni-quiche.sh — la terza candidata di B2 alla prova dell'SNI.
#
#   bash 01-b2-sni-quiche.sh leggi        clona e LEGGE (produce la previsione)
#   bash 01-b2-sni-quiche.sh costruisci   costruisce il bersaglio
#   bash 01-b2-sni-quiche.sh controlla    dice solo che cosa c'e'
#
# ---------------------------------------------------------------------------
# PERCHE' DUE AZIONI E NON UNA
#
# ⛔ `LEZIONI.md` §1.11: per ogni prova si scrive PRIMA che aspetto avrebbe il
#    contrario.  Se leggere e misurare stanno nello stesso comando, la
#    previsione la si scrive dopo aver visto il risultato — cioe' non la si
#    scrive affatto.  Qui `leggi` finisce prima che il bersaglio esista.
#
# ---------------------------------------------------------------------------
# IL CRITERIO, E PERCHE' VIENE PRIMA DEL COLLANTE
#
# `DECISIONI.md` §6.4: la libreria DEVE servire un certificato a chi non manda
# SNI, perche' chi si collega a un INDIRIZZO IP non lo manda e quello e' il
# caso primario del prodotto.  Il 9 agosto 2026 `lsquic` e' uscita per questo,
# dopo 333 righe di collante; il 10 `ngtcp2` l'ha passata in una connessione.
#
# ⚠ E su `quiche` c'e' una ragione in piu' per non fidarsi della lettura: il
#   TLS non lo montiamo noi come su `ngtcp2` — se lo monta lei, dentro, in
#   Rust.  Cioe' e' esattamente la situazione di `lsquic`, dove la scelta del
#   certificato e' della libreria e non nostra.
#
# ---------------------------------------------------------------------------
# L'ATTESO, DICHIARATO PRIMA (regola B0.4)
#
#   1. quiche si clona con i suoi sottomoduli          -> atteso: si'
#   2. la libreria con l'API C compila                 -> atteso: si'
#   3. il loro esempio HTTP/3 in C si costruisce       -> atteso: si'
#   4. ⛔ il binario ESISTE davvero                     -> atteso: si'
#
# ⛔ Il punto 4 e' il controllo del 10 agosto ripetuto: non si guarda l'uscita
#    di make, si guarda se il file c'e'.  Un `make` che non ha niente da fare
#    esce con zero.
#
# ---------------------------------------------------------------------------
# ⭐ LA PREVISIONE, SCRITTA PRIMA DI COSTRUIRE — `[R]` 10 agosto 2026
#
# Prodotta da `bash 01-b2-sni-quiche.sh leggi`, su 81 file di 3 alberi, con il
# controllo positivo che risponde ('quiche' in 33 file):
#
#   select_certificate_cb ......... 0 file
#   servername / SNI .............. 1 file
#   caricamento del certificato ... 11 file
#
# L'unica occorrenza e' `quiche/src/tls/mod.rs:510-526`, ed e' un LETTORE:
#
#     pub fn server_name(&self) -> Option<&str>   ->  SSL_get_servername(...)
#         if ptr.is_null() { return None }
#
# cioe' espone al chiamante che cosa ha mandato il pari, e lo passa al C come
# `quiche_conn_server_name()` (`ffi.rs:1232`).  ⭐ **Restituisce `Option`**:
# «nessun SNI» e' uno stato legittimo che la firma sa rappresentare, non un
# errore.  Nessuno cerca il certificato per nome: quello sta nella `Config`
# (`load_cert_chain_from_pem_file`) e si serve sempre.
#
# ⇒ **PREVISIONE: passa.**
#
# ⭐ Che aspetto avrebbe il contrario: la stretta di mano che cade come su
#    `lsquic` — e allora la candidata esce QUI, in una connessione, invece che
#    dopo il collante.  E vorrebbe dire che il rifiuto sta in un punto che
#    questa lettura non ha visto: dentro BoringSSL, o in codice generato.
#
# ⚠ E resta la ragione per diffidare comunque: come `lsquic` e a differenza di
#   `ngtcp2`, qui il TLS se lo monta la libreria.  La lettura non e' la misura.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
Q="$SRC/quiche"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-costruisci}

log "Stato di partenza"
inf "cargo    $(cargo --version 2>/dev/null || echo MANCA)"
inf "rustc    $(rustc --version 2>/dev/null || echo MANCA)"
inf "go       $(go version 2>/dev/null || echo MANCA)"
inf "cmake    $(cmake --version 2>/dev/null | head -1 || echo MANCA)"
if ! command -v cargo >/dev/null; then
	ko "cargo manca: sta in fondamenta/banco/provision.sh, non si installa a mano"
	exit 2
fi
[ -d "$Q" ] && inf "quiche gia' clonato" || inf "quiche da clonare"

[ "$AZIONE" = controlla ] && exit 0

# ---------------------------------------------------------------------------
# 1. Il clone.  ⚠ `--recursive`: quiche si porta dentro BoringSSL come
#    sottomodulo, e senza il clone riesce e la costruzione fallisce dopo.
# ---------------------------------------------------------------------------
if [ ! -d "$Q" ]; then
	log "Clone di quiche"
	# ⚠ Niente `-b <ramo>`: il ramo predefinito e' di chi lo pubblica, non
	#   nostro (la lezione di BoringSSL, 9 agosto).
	git clone --depth 1 --recursive https://github.com/cloudflare/quiche "$Q" \
		|| { ko "clone fallito"; exit 3; }
fi
inf "versione $(cd "$Q" && git describe --tags 2>/dev/null || echo '(senza tag)')"
if [ ! -d "$Q/quiche/deps/boringssl" ] && [ ! -d "$Q/quiche/deps" ]; then
	inf "⚠ nessuna cartella deps: quiche potrebbe costruire BoringSSL da se'"
fi

# ---------------------------------------------------------------------------
# 2. ⛔ LA LETTURA, cioe' la previsione.  Si cerca CHI sceglie il certificato.
#
# La domanda non e' «c'e' la parola SNI»: e' «esiste un punto in cui il
# certificato viene cercato PER NOME, e che puo' fallire?».  Su `lsquic` quel
# punto c'era ed era fatale; su `ngtcp2` non c'era affatto.
# ---------------------------------------------------------------------------
if [ "$AZIONE" = leggi ]; then
	log "La lettura: chi sceglie il certificato in quiche"
	# ⚠ Gli esempi in C stanno in `quiche/examples`, non in `examples`:
	#   il deposito ha una cassetta per ogni pezzo e una si chiama come il
	#   deposito.  Il primo giro ha cercato nel posto sbagliato — e il banco
	#   l'ha DETTO invece di contare zero.
	ALBERI=("$Q/quiche/src" "$Q/apps/src" "$Q/quiche/examples")
	for a in "${ALBERI[@]}"; do
		if [ ! -d "$a" ]; then
			ko "l'albero $a non esiste: la ricerca non si puo' fare"
			exit 4
		fi
	done
	# ⛔ Il denominatore, sempre: su quanti file si sta guardando.
	FILE_TOT=$(find "${ALBERI[@]}" \( -name '*.rs' -o -name '*.c' -o -name '*.h' \) | wc -l)
	inf "si guarda dentro $FILE_TOT file di ${#ALBERI[@]} alberi"
	if [ "$FILE_TOT" -lt 20 ]; then
		ko "solo $FILE_TOT file: la ricerca sta guardando nel posto sbagliato"
		exit 4
	fi

	cerca()
	{
		local etichetta=$1 modello=$2
		local n
		# ⚠ Niente `2>/dev/null`: se grep si lamenta, si deve vedere.
		n=$(grep -rIl --include='*.rs' --include='*.c' --include='*.h' \
			-e "$modello" "${ALBERI[@]}" | wc -l)
		printf '    --  %-42s %s file\n' "$etichetta" "$n" >&2
		echo "$n"
	}

	N1=$(cerca "select_certificate_cb"          "select_certificate_cb")
	N2=$(cerca "tlsext_servername / SNI"        "servername\|tlsext_servername\|SNI")
	N3=$(cerca "il caricamento del certificato" "load_cert_chain\|use_certificate")
	CTRL=$(cerca "controllo positivo: 'quiche'" "quiche")
	if [ "$CTRL" -eq 0 ]; then
		ko "⛔ il controllo positivo e' FALLITO: zero file nominano 'quiche'"
		ko "   la ricerca non sta leggendo niente.  Nessun numero qui sopra vale."
		exit 4
	fi
	ok "controllo positivo: 'quiche' trovato in $CTRL file"

	printf '\n'
	log "La previsione"
	if [ "$N1" -eq 0 ] && [ "$N2" -eq 0 ]; then
		ok "nessuna ricerca del certificato per nome: la previsione e' PASSA"
		inf "⇒ il certificato e' legato alla configurazione e servito sempre"
	else
		inf "⚠ ci sono $N1 file con select_certificate_cb e $N2 che nominano SNI:"
		inf "  vanno LETTI prima di prevedere.  Un punto che sceglie per nome e'"
		inf "  un punto che puo' rifiutare — ed e' come e' uscita lsquic."
		grep -rn --include='*.rs' --include='*.c' --include='*.h' \
			-e "select_certificate_cb" -e "servername" "${ALBERI[@]}" | head -12 | sed 's/^/        /'
	fi
	inf "⛔ e comunque la lettura NON e' la misura: la misura e' una connessione"
	exit 0
fi

# ---------------------------------------------------------------------------
# 3. La costruzione: la libreria con l'API C, poi il loro esempio HTTP/3 in C
#
# ⚠ Il bersaglio e' il loro esempio in C e non l'applicazione in Rust: il
#   server di REMOTIX e' in C (§6.3), e quel che si vuole misurare e' la
#   strada che percorreremmo noi.  ⛔ E' anche l'unico modo perche' il numero
#   di righe di collante sia confrontabile con quello di ngtcp2.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔ 3-bis. LA VERSIONE, e non e' un dettaglio di costruzione
#
# `[M]` 10 agosto 2026, primo giro: il ramo predefinito e' `quiche` **0.29.3**,
# e cargo si e' fermato con
#
#     error: rustc 1.85.0 is not supported by the following packages:
#            quiche@0.29.3 requires rustc 1.88
#
# ⭐ Trixie ha **1.85**.  Cioe' la candidata piu' recente NON SI COSTRUISCE con
#    il compilatore della distribuzione su cui gira il prodotto, e la scelta e'
#    fra una versione piu' vecchia e una catena di strumenti fuori dai
#    pacchetti (`rustup`) — che e' un costo del prodotto, non del banco.
#
# ⛔ Il banco non lo aggira in silenzio: SCEGLIE la versione piu' recente che
#    il compilatore presente sa costruire, e stampa quale e perche'.  Il
#    numero che ne esce va scritto accanto alla misura, o la misura mente su
#    che cosa ha misurato.
# ---------------------------------------------------------------------------
log "La versione: quale quiche sa costruire questo rustc"
cd "$Q" || exit 5
RUSTV=$(rustc --version | awk '{print $2}')
inf "rustc presente: $RUSTV"

# ⚠ Un clone `--depth 1` non ha le etichette: senza questo, il ciclo qui sotto
#   non guarderebbe NESSUNA versione e direbbe «nessuna adatta» — uno zero da
#   una ricerca mai fatta, che e' il difetto del 9 agosto.
git fetch --tags --quiet origin
ETICHETTE=$(git tag -l '[0-9]*' | sort -V -r)
NUM_ET=$(printf '%s\n' "$ETICHETTE" | grep -c .)
inf "etichette viste nel deposito: $NUM_ET"
if [ "$NUM_ET" -lt 5 ]; then
	ko "solo $NUM_ET etichette: il fetch non ha portato niente, la scelta non vale"
	exit 5
fi

# Confronta due versioni con `sort -V`: vero se $1 <= $2.
minore_o_uguale() { [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -1)" = "$1" ]; }

SCELTA=""
for t in $ETICHETTE; do
	MANIFESTO=$(git show "$t:quiche/Cargo.toml" 2>/dev/null)
	[ -z "$MANIFESTO" ] && continue
	MSRV=$(printf '%s\n' "$MANIFESTO" | grep -m1 '^rust-version' | tr -d '"' | awk '{print $3}')
	[ -z "$MSRV" ] && continue
	if minore_o_uguale "$MSRV" "$RUSTV"; then
		SCELTA=$t
		inf "⭐ $t pretende rustc $MSRV  <=  $RUSTV: e' questa"
		break
	fi
	inf "   $t pretende rustc $MSRV: troppo nuova"
done
if [ -z "$SCELTA" ]; then
	ko "⛔ nessuna versione di quiche si costruisce con rustc $RUSTV"
	ko "   la candidata non e' eliminata: e' bloccata da una catena di strumenti,"
	ko "   e la decisione e' se portarne una fuori dai pacchetti.  Va scritto."
	exit 5
fi
git checkout --quiet "$SCELTA" && git submodule update --init --recursive --quiet
ok "quiche $SCELTA"
inf "⚠ la misura che segue vale per QUESTA versione, e il numero va scritto accanto"

# ---------------------------------------------------------------------------
# ⛔ 3-ter. SOLO IL PACCHETTO CHE CI SERVE
#
# `[M]` 10 agosto: anche con quiche 0.28.0 — che pretende esattamente 1.85 —
# cargo si ferma lo stesso, e NON per colpa di quiche: il deposito e' un
# `workspace` che contiene anche `tokio-quiche`, `h3i`, `qlog-dancer`, e quelli
# tirano dentro `tonic`, `icu`, `time`, `image` — pretese fino a 1.88.
#
# ⚠ La distinzione conta per la decisione: il costo NON e' «quiche non si
#   costruisce», e' «il loro deposito non si costruisce tutto intero».  Noi di
#   quel deposito useremmo un pacchetto solo.
#
# ⛔ Quindi si costruisce `-p quiche`, e se la risoluzione si impunta lo stesso
#    si allenta SOLO la risoluzione (`incompatible-rust-versions = allow`) —
#    che riguarda pacchetti che non compileremo mai.  Non e' un aggiramento
#    nascosto: e' stampato, e il fatto che sia servito e' un dato di §6.4.
# ---------------------------------------------------------------------------
log "La libreria con l'API C (solo il pacchetto quiche)"
cargo build --release --features ffi -p quiche
STATO=$?
if [ "$STATO" -ne 0 ]; then
	inf "⚠ la risoluzione si impunta sui fratelli del workspace: la allento"
	inf "  (CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=allow) — riguarda"
	inf "  pacchetti che questo comando non compila"
	CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=allow \
		cargo build --release --features ffi -p quiche
	STATO=$?
fi
inf "cargo e' uscito con $STATO"
LIB=$(find "$Q/target/release" -maxdepth 1 -name 'libquiche.a' -o -maxdepth 1 -name 'libquiche.so' | head -1)
if [ -z "$LIB" ]; then
	ko "⛔ nessuna libquiche.a/.so in $Q/target/release"
	ls -la "$Q/target/release" 2>&1 | head -20 | sed 's/^/        /'
	exit 5
fi
ok "costruita: $LIB"

log "L'esempio HTTP/3 in C"
inf "che cosa c'e' in quiche/examples/:"
ls "$Q/quiche/examples" | sed 's/^/        /'
if [ -f "$Q/quiche/examples/Makefile" ]; then
	make -C "$Q/quiche/examples" http3-server
	STATO=$?
	inf "make e' uscito con $STATO"
else
	ko "nessun Makefile in quiche/examples/: va guardato a mano che cosa offrono"
	exit 6
fi

SERVER="$Q/quiche/examples/http3-server"
log "Esito"
if [ ! -f "$SERVER" ] && [ "$STATO" -ne 0 ]; then
	ko "⛔ la costruzione dell'esempio e' fallita (make: $STATO): l'errore e' qui sopra"
	exit 6
fi
if [ ! -f "$SERVER" ]; then
	ko "⛔ make e' uscito con 0 e $SERVER NON esiste"
	exit 6
fi
ok "http3-server costruito"
inf "$(ls -la "$SERVER" | sed 's/  */ /g')"

# ⚠ Il conto delle righe: e' la colonna «quanto collante» di §6.4.
#   ⛔ E NON e' confrontabile alla cieca con le 7.041 di ngtcp2: quello e' il
#      loro HTTP/3 completo in C++, questo e' un esempio minimo in C.  Il
#      numero si scrive con la sua etichetta, o mente.
log "Quanto pesa il loro esempio — il dato di §6.4"
N=$(wc -l < "$Q/quiche/examples/http3-server.c")
inf "quiche/examples/http3-server.c: $N righe"
inf "⚠ e' un esempio MINIMO in C: non si confronta con le 7.041 di ngtcp2,"
inf "  che sono il loro HTTP/3 completo in C++.  Due numeri, due etichette."

printf '\n'
ok "il bersaglio e' pronto: adesso la misura, con 01-b2-sonda-sni.py"
exit 0
