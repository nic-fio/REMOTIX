#!/bin/bash
#
# 01-p1-dentro.sh — la meta' di P1 che gira DENTRO il contenitore.
#
#   bash /srv/src/01-p1-dentro.sh fumo        accende, prova, spegne
#   bash /srv/src/01-p1-dentro.sh controlli   i controlli positivi dello strumento
#
# ⛔ NON si lancia a mano: lo chiama `01-p1-prodotto.sh`, che sta fuori dal
#    contenitore e sceglie la porta d'ingresso.  Qui dentro non si sa nulla di
#    `enter.sh` ne' di `unshare`.
#
# -----------------------------------------------------------------------------
# ⛔ NON PARLA — STAMPA FATTI, E IL VERDETTO LO DA' CHI LO CHIAMA (`PIANO.md`
#    §0.3, regola B0.4).  Il protocollo e' una riga per fatto:
#
#      FATTO <nome> <0|1> <dettaglio libero fino a fine riga>
#
#    dove `1` vuol dire «la cosa attesa e' successa».  ⚠ Tutto il resto che
#    esce di qui e' rumore per l'uomo, e chi legge lo ignora: cosi' un `curl`
#    che stampa in mezzo non puo' cambiare un esito.
#
# -----------------------------------------------------------------------------
# ⛔ I CONFINI, E SONO DI SESSIONE (mandato dell'11 agosto 2026)
#
#   · ⛔ **porta 7448**, mai la 7447: la 7447 e' `bsslserver`, l'innesto, e ci
#     contano altri banchi.  Qui non si tocca ne' si guarda;
#   · ⛔ **nessuna autenticazione**: §4.4-bis banna l'indirizzo per 12 ore dopo
#     tre parole d'ordine sbagliate, e questo banco non ha nessun motivo di
#     rischiarlo (regola B0.3).  La prova di fumo si ferma **prima** del filo
#     RCP: guarda la pagina, le intestazioni, i due ascoltatori e il socket di
#     comando.  ⚠ Quel che questo banco NON prova va letto qui, non dedotto:
#     stretta di mano, `SESSIONE`, ban, sblocco — sono di B7, B8 e B10;
#   · ⛔ tutto quel che scrive sta in `/srv/src/tmp/p1-*`: file dei ban, socket
#     di comando, certificati, registro.  Nessun altro banco li nomina.
# -----------------------------------------------------------------------------
set -uo pipefail

# ⛔⭐ `D` E `PREFISSO_TMP` SI POSSONO CAMBIARE — dichiarato la sera dell'11
#     agosto 2026, per la certificazione di P1 sotto B12.
#
# `D` era scritto dentro, e voleva dire che questo banco poteva accendere solo
# l'unico prodotto della macchina.  ⛔ La certificazione vuole tre giri di cui
# uno col codice guasto: farli sul prodotto di casa lascerebbe, per qualche
# minuto, un binario bugiardo sotto i piedi di chiunque altro lo riaccendesse.
# ⭐ Da qui in poi `01-p1-prodotto.sh` passa `D`, `PORTA`, `PORTA_MORTA` e
#    `PREFISSO_TMP` davanti a `bash`, e i valori predefiniti sono quelli di
#    prima: chi lancia a mano misura quel che misurava.
D=${D:-/srv/src/remotix}
TMP=/srv/src/tmp
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7448}
PORTA_MORTA=${PORTA_MORTA:-7449}   # dove non c'e' nessuno, e serve che non ci sia
# ⛔ Il prefisso tiene separati i file di due giri che vivono insieme: cinque
#    agenti sulla stessa macchina la sera dell'11 agosto 2026, e un file dei ban
#    condiviso e' esattamente lo stato che sopravvive di B0.2.
PREFISSO_TMP=${PREFISSO_TMP:-p1}

CERT=$TMP/$PREFISSO_TMP-cert
BAN=$TMP/$PREFISSO_TMP-ban
SOCK=$TMP/$PREFISSO_TMP-comando
LOG=$TMP/$PREFISSO_TMP-server.log
PIDF=$TMP/$PREFISSO_TMP-server.pid

mkdir -p "$TMP"

fatto() { printf 'FATTO %s %s %s\n' "$1" "$2" "${3-}"; }
nota()  { printf '    --  %s\n' "$*"; }
tit()   { printf '\n== %s\n' "$*"; }

# -----------------------------------------------------------------------------
# ⛔ La sonda della pagina, e vive due volte: una contro il server acceso, una
#    contro una porta dove NON c'e' nessuno.  ⭐ E' il controllo positivo dello
#    strumento (`LEZIONI.md` §1.9 regola 2): se la stessa sonda dice OK anche
#    dove non c'e' niente, gli OK di sopra non valgono.
#
# ⚠ `curl` scrive lo stato HTTP con `-w`, e lo stato d'uscita di curl si legge
#   a parte: «connessione rifiutata» e «404» sono due fatti diversi, e senza
#   questa distinzione avrebbero la stessa faccia (§1.9 regola 1).
sonda_get() # $1 = porta, $2 = percorso, $3 = file testa, $4 = file corpo
{
	local stato
	stato=$(curl -sk --max-time 10 -D "$3" -o "$4" \
	        -w '%{http_code}' "https://$IND:$1$2" 2>/dev/null)
	printf '%s %s\n' "$?" "${stato:-000}"
}

# -----------------------------------------------------------------------------
fase_fumo()
{
	local pid imp uscita stato n

	tit "Lo stato iniziale della porta $PORTA"
	# ⛔ «vuoto» e «proibito» hanno la stessa faccia: si stampa il conteggio E
	#    lo stato d'uscita di `ss`, non uno dei due.
	n=$(ss -lun 2>/dev/null | grep -c ":$PORTA\b"); stato=$?
	nota "ss -lun: $n righe su :$PORTA (stato d'uscita del filtro: $stato)"
	if command -v ss >/dev/null; then
		fatto porta.libera.prima "$([ "$n" -eq 0 ] && echo 1 || echo 0)" \
		      "righe UDP su :$PORTA prima di accendere = $n"
	else
		fatto porta.libera.prima 0 "⛔ «ss» non c'e' nel contenitore: non ho guardato"
	fi

	tit "Si accende il prodotto sulla porta $PORTA"
	rm -rf "$CERT"; rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
	if [ ! -x "$D/remotix" ]; then
		fatto acceso 0 "⛔ $D/remotix non c'e' o non e' eseguibile"
		return 2
	fi
	nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
	      --certificati "$CERT" --pagina "$D/pagina.html" \
	      --ban "$BAN" --comando-socket "$SOCK" --parlantina \
	      > "$LOG" 2>&1 &
	pid=$!
	echo "$pid" > "$PIDF"
	sleep 3

	# ⛔ `[ -d /proc/PID ]` e non `kill -0`: su un processo di un altro utente
	#    `kill -0` risponde «operazione non permessa», che non e' «non esiste»
	#    (`LEZIONI.md` §1.9, la sesta veste).
	if [ -d "/proc/$pid" ]; then
		fatto acceso 1 "pid $pid vivo dopo 3 s"
	else
		fatto acceso 0 "il processo e' morto subito; registro qui sotto"
		cat "$LOG"
		return 2
	fi

	tit "Il registro d'avvio"
	cat "$LOG"

	tit "I due certificati e i permessi delle chiavi"
	ls -l "$CERT" 2>&1
	n=$(ls "$CERT"/*.pem 2>/dev/null | wc -l)
	fatto certificati.due "$([ "$n" -eq 2 ] && echo 1 || echo 0)" \
	      "$n file .pem in $CERT (attesi 2: sessione e ospite)"
	stato=$(stat -c '%a' "$CERT"/sessione.key 2>/dev/null)
	fatto chiave.0600 "$([ "$stato" = 600 ] && echo 1 || echo 0)" \
	      "permessi di sessione.key: ${stato:-(non leggibile)}"

	# ⛔ L'impronta si calcola con `openssl`, cioe' con un programma che non e'
	#    nostro: se la calcolasse il server e poi la confrontasse con se stessa,
	#    il confronto sarebbe vero anche se il server sbaglia (`LEZIONI.md`
	#    §1.9 regola 5 — un denominatore si legge dove la cosa succede).
	imp=$(openssl x509 -in "$CERT/sessione.pem" -outform der 2>/dev/null \
	      | openssl dgst -sha256 -binary | base64 -w0)
	nota "impronta calcolata da openssl: ${imp:-(nessuna)}"
	fatto impronta.calcolata "$([ -n "$imp" ] && echo 1 || echo 0)" \
	      "sha256 del DER di sessione.pem, in base64: ${imp:-(vuota)}"

	tit "GET / in TLS"
	uscita=$(sonda_get "$PORTA" "/" "$TMP/$PREFISSO_TMP-testa.txt" "$TMP/$PREFISSO_TMP-corpo.html")
	nota "curl: stato d'uscita $(echo "$uscita" | cut -d' ' -f1), stato HTTP $(echo "$uscita" | cut -d' ' -f2)"
	fatto pagina.200 "$([ "$uscita" = "0 200" ] && echo 1 || echo 0)" \
	      "curl uscita+stato = «$uscita» (atteso «0 200»)"
	nota "corpo servito: $(stat -c%s "$TMP/$PREFISSO_TMP-corpo.html" 2>/dev/null || echo 0) byte"

	# ⛔ Un nome per ciascuna, e non uno solo per tutte e tre: la prima stesura
	#    le chiamava tutte «isolamento.Origin» — tre righe con la stessa chiave
	#    nel registro, e chi ne avesse letta una sola avrebbe creduto di aver
	#    letto le altre due (giro delle 04:52 dell'11 agosto 2026).
	tit "Le tre intestazioni di isolamento (SPECIFICHE.md §11.5)"
	for coppia in "coop|Cross-Origin-Opener-Policy: same-origin" \
	              "coep|Cross-Origin-Embedder-Policy: require-corp" \
	              "corp|Cross-Origin-Resource-Policy: same-origin"; do
		nome=${coppia%%|*}; h=${coppia#*|}
		if grep -a -i -F -q "$h" "$TMP/$PREFISSO_TMP-testa.txt" 2>/dev/null; then
			fatto "isolamento.$nome" 1 "$h"
		else
			fatto "isolamento.$nome" 0 "MANCA: $h"
		fi
	done

	tit "L'impronta DENTRO la pagina servita"
	if [ -n "$imp" ] && grep -a -F -q "$imp" "$TMP/$PREFISSO_TMP-corpo.html" 2>/dev/null; then
		fatto pagina.impronta 1 "la pagina porta l'impronta calcolata da openssl"
	else
		fatto pagina.impronta 0 "la pagina NON porta l'impronta di openssl"
		grep -a -o 'IMPRONTA_SERVITA = "[^"]*"' "$TMP/$PREFISSO_TMP-corpo.html" 2>/dev/null
	fi
	if grep -a -F -q "__IMPRONTA__" "$TMP/$PREFISSO_TMP-corpo.html" 2>/dev/null; then
		fatto pagina.segni 0 "il segno __IMPRONTA__ e' rimasto non sostituito"
	else
		fatto pagina.segni 1 "nessun segno __…__ rimasto nella pagina servita"
	fi

	tit "GET /impronta (RCP.md §4.1-bis)"
	uscita=$(sonda_get "$PORTA" "/impronta" "$TMP/$PREFISSO_TMP-testa2.txt" "$TMP/$PREFISSO_TMP-imp.json")
	cat "$TMP/$PREFISSO_TMP-imp.json" 2>/dev/null; printf '\n'
	if [ -n "$imp" ] && grep -a -F -q "$imp" "$TMP/$PREFISSO_TMP-imp.json" 2>/dev/null; then
		fatto endpoint.impronta 1 "«$uscita», e serve l'impronta corrente"
	else
		fatto endpoint.impronta 0 "«$uscita», e NON serve l'impronta corrente"
	fi

	tit "GET /qualcosa-che-non-esiste"
	uscita=$(sonda_get "$PORTA" "/nulla-11ago" "$TMP/$PREFISSO_TMP-testa3.txt" /dev/null)
	fatto pagina.404 "$([ "$uscita" = "0 404" ] && echo 1 || echo 0)" \
	      "curl uscita+stato = «$uscita» (atteso «0 404»)"

	tit "I due ascoltatori con lo stesso numero di porta (RCP.md §2.4)"
	ss -lun 2>/dev/null | grep ":$PORTA\b" || true
	ss -ltn 2>/dev/null | grep ":$PORTA\b" || true
	n=$(ss -lun 2>/dev/null | grep -c ":$PORTA\b")
	fatto ascolto.udp "$([ "$n" -ge 1 ] && echo 1 || echo 0)" "righe UDP su :$PORTA = $n"
	n=$(ss -ltn 2>/dev/null | grep -c ":$PORTA\b")
	fatto ascolto.tcp "$([ "$n" -ge 1 ] && echo 1 || echo 0)" "righe TCP su :$PORTA = $n"

	# ⛔ Il socket di comando si prova con PING/PONG, non con SBLOCCA: uno
	#    sblocco qui dentro non prova niente (non c'e' nessun ban) e la regola
	#    B0.3 vuole che chi sblocca lo dichiari.  ⭐ Questo banco NON sblocca
	#    mai: non autentica, quindi non banna.
	tit "Il socket di comando: PING → PONG"
	stato=$(python3 - "$SOCK" <<-'PY' 2>&1
	import socket, sys
	try:
	    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	    s.settimeout(5)
	    s.connect(sys.argv[1])
	    s.sendall(b"PING\n")
	    print(s.recv(64).decode(errors="replace").strip())
	except Exception as e:
	    print("ERRORE:%s" % e)
	PY
	)
	nota "risposta: «$stato»"
	fatto comando.pong "$([ "$stato" = PONG ] && echo 1 || echo 0)" \
	      "PING sul socket $SOCK → «$stato» (atteso «PONG»)"

	# -------------------------------------------------------------------------
	tit "Si spegne, e si guarda se e' bastato TERM"
	kill -TERM "$pid" 2>/dev/null
	for _ in 1 2 3 4 5 6 7 8 9 10; do
		[ -d "/proc/$pid" ] || break
		sleep 0.5
	done
	if [ -d "/proc/$pid" ]; then
		kill -KILL "$pid" 2>/dev/null
		fatto spento.pulito 0 "⛔ TERM non e' bastato in 5 s: ho dovuto usare KILL"
	else
		fatto spento.pulito 1 "TERM e' bastato: il processo $pid non c'e' piu'"
	fi

	sleep 1
	n=$(ss -lun 2>/dev/null | grep -c ":$PORTA\b")
	fatto porta.libera.dopo "$([ "$n" -eq 0 ] && echo 1 || echo 0)" \
	      "righe UDP su :$PORTA dopo lo spegnimento = $n"

	tit "Il registro completo del giro"
	cat "$LOG"
	# ⛔ Il congedo si legge nel registro del server, non si deduce dal fatto
	#    che il processo sia uscito: `src/main.c` congeda tutti con
	#    SERVER_IN_CHIUSURA prima di uscire, e se non lo facesse il processo
	#    morirebbe lo stesso (fasi/01-filo-nudo.md, il riquadro su 0x0C).
	if grep -a -q -i -e 'chiusur' -e 'CHIUSURA' "$LOG" 2>/dev/null; then
		fatto spento.dichiarato 1 "il registro nomina la chiusura"
	else
		fatto spento.dichiarato 0 "il registro NON nomina nessuna chiusura"
	fi
	return 0
}

# -----------------------------------------------------------------------------
# ⛔⭐ I CONTROLLI POSITIVI DELLO STRUMENTO — punto 5 del mandato.
#
# La domanda a cui rispondono e' una sola: *come fa questo banco a sapere che
# saprebbe accorgersi di un fallimento?*  Ciascuno **deve uscire rosso**, e se
# esce verde e' il banco a essere rotto, non il prodotto.
fase_controlli()
{
	local g=$TMP/$PREFISSO_TMP-guasto out stato

	# -- C1 -------------------------------------------------------------------
	# ⛔ L'OTTAVA VESTE DI §1.9, RIPRODOTTA: «il file c'e'» e «il file e' quello
	#    che ho appena costruito» sono due domande diverse.  Si mette un binario
	#    BUONO al posto giusto, si rompe un sorgente, si costruisce: se
	#    `costruisci.sh` si difende come dichiara, il binario buono dev'essere
	#    SPARITO e l'esito dev'essere diverso da zero.  ⚠ Un banco che
	#    controllasse `test -x` direbbe verde — ed e' esattamente il difetto che
	#    accese il server sano credendo di aver acceso quello guasto.
	#
	# ⚠ Si lavora su una COPIA: il prodotto non si tocca mai.
	rm -rf "$g"; mkdir -p "$g"
	cp "$D"/*.c "$D"/*.h "$D"/Makefile "$D"/costruisci.sh "$D"/pagina.html \
	   "$D"/remotix.pam "$g"/ 2>/dev/null
	cp "$D/remotix" "$g/remotix" 2>/dev/null
	printf '\n/* guasto innestato da 01-p1 */ questo non e del C valido;\n' >> "$g/registro.c"

	tit "C1 — costruzione guasta: l'esito dev'essere rosso e il binario dev'essere sparito"
	nota "copia in $g, guasto in registro.c, binario buono messo li' prima"
	GEMELLO=/srv/src/rcp bash "$g/costruisci.sh" > "$TMP/$PREFISSO_TMP-c1.log" 2>&1
	stato=$?
	nota "costruisci.sh e' uscito $stato"
	tail -n 12 "$TMP/$PREFISSO_TMP-c1.log"
	fatto c1.esito.rosso "$([ "$stato" -ne 0 ] && echo 1 || echo 0)" \
	      "costruisci.sh su sorgente guasto e' uscito $stato (atteso ≠ 0)"
	if [ -e "$g/remotix" ]; then
		fatto c1.binario.sparito 0 \
		      "⛔ il binario buono e' ancora li': «test -x» direbbe verde su una costruzione FALLITA"
	else
		fatto c1.binario.sparito 1 \
		      "il binario buono e' sparito: «c'e'» non puo' piu' voler dire «e' di ieri»"
	fi
	rm -rf "$g"

	# -- C2 -------------------------------------------------------------------
	# ⛔ La sonda della pagina puntata dove NON c'e' nessuno.  Se dicesse «0 200»
	#    anche qui, tutti gli OK della fase di fumo sarebbero senza valore.
	tit "C2 — la sonda della pagina contro la porta $PORTA_MORTA, dove non c'e' nessuno"
	out=$(sonda_get "$PORTA_MORTA" "/" "$TMP/$PREFISSO_TMP-c2-testa.txt" "$TMP/$PREFISSO_TMP-c2-corpo.html")
	nota "curl uscita+stato: «$out»"
	fatto c2.sonda.rossa "$([ "$out" != "0 200" ] && echo 1 || echo 0)" \
	      "sonda su :$PORTA_MORTA → «$out» (atteso ≠ «0 200»)"

	# -- C3 -------------------------------------------------------------------
	# ⛔ Lo strumento che cerca le marche dentro il binario: sa dire di NO?  E sa
	#    dire di SI' su qualcosa che c'e' di sicuro?  Le due domande insieme,
	#    perche' una sola non basta (`LEZIONI.md` §1.9 regola 2).
	tit "C3 — il cercatore di marche: sa dire NO, e sa dire SI'"
	if grep -a -F -q -e "MARCA-INESISTENTE-01P1-11AGO2026" "$D/remotix"; then
		fatto c3.dice.no 0 "⛔ ha trovato una marca inventata: il cercatore e' rotto"
	else
		fatto c3.dice.no 1 "la marca inventata NON c'e', come dev'essere"
	fi
	if grep -a -F -q -e "GCC:" "$D/remotix"; then
		fatto c3.dice.si 1 "trova «GCC:», che in un binario compilato c'e' di sicuro"
	else
		fatto c3.dice.si 0 "⛔ non trova nemmeno «GCC:»: i NO del cercatore non valgono niente"
	fi
	return 0
}

case "${1:-}" in
	fumo)      fase_fumo ;;
	controlli) fase_controlli ;;
	*) printf 'uso: %s fumo|controlli\n' "$0" >&2; exit 2 ;;
esac
