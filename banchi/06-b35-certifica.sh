#!/bin/bash
#
# 06-b35-certifica.sh — ⭐ IL CONTROLLO POSITIVO della sottofase 6.3.
#
#   sudo bash .../06-b35-certifica.sh          tutti i guasti
#   sudo bash .../06-b35-certifica.sh G1 G3    solo quelli
#
# ⛔ GIRA SUL SERVER, DA ROOT: accende e spegne il server sulla 7731, e chiama
#    il client dentro il contenitore (da root `enter.sh` non chiede niente).
#
# ===========================================================================
# ⛔ CHE COSA CERTIFICA, E CHE COSA NO
# ===========================================================================
#
# `CODER.md` §3.3: *«accerta che il banco sappia produrre il risultato atteso
# prima di puntarlo sull'incognita»*.  ⇒ Si innesta un guasto **su una copia**
# dell'albero e si pretende che `06-b35-tela.py` diventi rosso **nel caso
# dichiarato prima** — non «che diventi rosso qualcosa».
#
# ⛔ Il modello e' `banchi/04-b31-certifica.sh`, che innesta 12 guasti.  ⚠ Qui
#    sono cinque e non dodici, e la ragione va detta: quel banco monta `rcp.c`
#    **nudo** e un giro costa millisecondi; ⛔ qui ogni guasto costa una
#    ricompilazione, un riavvio del server e un giro su un compositore vero —
#    circa un minuto e mezzo l'uno.  ⇒ Cinque scelti perche' hanno attesi
#    **distinguibili fra loro**, che e' quel che rende il controllo una prova.
#
# ⚠ E l'albero guasto e' un albero SUO (`06-p-guasto`): il sano non si tocca
#   mai, cosi' un giro interrotto a meta' non lascia un guasto in produzione.
#
# ⛔ IL PALCO SI GIUDICA PRIMA: se il client esce con 5 («IL PALCO, NON IL
#    PRODOTTO») il caso NON si conta ne' come verde ne' come rosso — si dichiara
#    «non misurato», perche' un compositore che non consegna e un difetto hanno
#    la stessa faccia (`CODER.md` §3.10).
set -uo pipefail

SANO=${SANO:-/media/REMOTIX/src/06-p-src}
GUASTO=${GUASTO:-/media/REMOTIX/src/06-p-guasto}
LAV=${LAV:-/media/REMOTIX/tmp/06-p}
PORTA=${PORTA:-7731}
UTENTE=${UTENTE:-provap6}
PAROLA=${PAROLA:-provap6-2026}
T="$SANO/banchi/06-b35-terreno.sh"
G="$SANO/banchi/06-b35-guasti.py"

# ⛔⭐ I PERCORSI DENTRO IL CONTENITORE NON SONO QUELLI DI FUORI, e confonderli
#     e' un errore che si presenta come «il file della parola non c'e'» — cioe'
#     come un difetto del banco che sembra un difetto di PAM.
#     `enter.sh` monta `/media/REMOTIX/src` su `/srv/src` e `/media/REMOTIX` su
#     `/srv/remotix`: tutto quel che si passa al client va tradotto.
C_GUASTO=${C_GUASTO:-/srv/src/06-p-guasto}
C_LAV=${C_LAV:-/srv/remotix/tmp/06-p}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }

QUALI=${*:-G1 G2 G3 G4 G5}
ESITI="$LAV/06-b35-certifica.txt"
: > "$ESITI"

# ⛔ La parola d'ordine sta in un file 0600 e una `trap` lo cancella (difetto
#    D12): non passa mai dalla riga di comando, nemmeno qui dentro.
P="$LAV/parola-certifica"
trap 'rm -f "$P"' EXIT
# ⛔⭐ E `umask 077` sta SOLO attorno a questo file, in una sottoshell.
#
#     Difetto del BANCO trovato misurando, 16 agosto 2026: messo in cima allo
#     script, l'umask valeva anche per la COMPILAZIONE fatta da root ⇒
#     `remotix` nasceva `0700 root:root`, e il figlio — che scende a uid 1008 —
#     usciva con **37, «non ha potuto eseguire il binario del server»**.
#     ⚠ Il sintomo era `CONGEDO 0x10 «la sessione grafica e' terminata»` su
#     tutti e cinque i guasti: il banco stava per scrivere cinque
#     «ATTESO-SMENTITO» accusando il prodotto dei propri permessi.
#     ⭐ E il prodotto lo diceva per esteso in una riga di registro — bastava
#     leggerla (`LEZIONI.md` §6.2-ter: il numero era gia' nel registro).
( umask 077; printf '%s\n' "$PAROLA" > "$P" )
chmod 600 "$P"
# ⛔ E il proprietario e' l'utente del CONTENITORE (uid 1000), non root: il
#    client gira li' dentro, e un file 0600 di root sarebbe illeggibile —
#    l'errore si presenterebbe come «PAM dice di no», cioe' come un difetto del
#    prodotto invece che del banco.
chown 1000:1000 "$P"

log "L'albero guasto: $GUASTO (copia di $SANO)"
rm -rf "$GUASTO"
cp -a "$SANO" "$GUASTO" || { ko "⛔ la copia non e' riuscita"; exit 2; }
# ⛔ E l'albero guasto dev'essere ATTRAVERSABILE ed ESEGUIBILE dall'utente del
#    banco: il figlio scende a uid 1008 e fa `execve` del binario che sta qui.
chmod -R a+rX "$GUASTO"
ok "copiato, e leggibile dall'utente del banco"

giro() {   # $1 = etichetta · $2 = albero da cui prendere il client (difetto: guasto)
	local albero=${2:-$C_GUASTO}
	bash /media/REMOTIX/enter.sh \
		"python3 $albero/banchi/06-b35-tela.py --porta $PORTA \
		 --utente $UTENTE --parola-file $C_LAV/parola-certifica --lavoro $C_LAV \
		 --giro dieci --coda 3 --etichetta $1 \
		 --scena 'controllo positivo: gnome-terminal a 50 ms'" \
		> "$LAV/certifica-$1.txt" 2>&1
	echo $?
}

# ⛔⛔ IL CONTROLLO POSITIVO DELLO STRUMENTO CHE CONTA — rilievo della revisione
#     avversariale, 21 agosto 2026.
#
#     `bash "$T" registro-tela 2>/dev/null | grep -ac ...` valeva **0** in due
#     casi che non si somigliano per niente:
#       · il registro c'e', e quella riga non c'e'   ⇒ una MISURA
#       · il registro non si legge, o la marca e' scaduta, o `D` e' sbagliato
#         ⇒ uno STRUMENTO CIECO
#     ⚠ E lo `2>/dev/null` cancellava proprio il messaggio che li distingue.
#     ⛔ Il guaio non e' teorico: «0» e' **esattamente** il valore che la regola
#     di G3 (`tela_nuova_dal_palco == 0`) pretende.  Un banco cieco avrebbe
#     scritto `ATTESO-CONFERMATO` senza aver guardato niente.
#
# ⇒ Qui il registro si legge UNA volta in un file, si guarda lo stato d'uscita,
#   e si pretende che lo strumento veda **qualcosa che c'e' di sicuro**: un
#   giro che ha parlato col server lascia SEMPRE righe della tela.  Se non ne
#   trova nemmeno una, lo strumento e' cieco e il caso NON si misura.
leggi_registro() {   # $1 = D (albero dei sorgenti) · $2 = file in cui scrivere
	local d=$1 fuori=$2 u n
	D="$d" bash "$T" registro-tela > "$fuori" 2> "$fuori.errori"
	u=$?
	if [ $u -ne 0 ]; then
		ko "⛔ «registro-tela» e' uscito con $u:"
		sed 's/^/            /' < "$fuori.errori"
		return 1
	fi
	n=$(wc -l < "$fuori"); [ -n "$n" ] || n=0
	if [ "$n" -eq 0 ]; then
		ko "⛔ ZERO righe della tela nel registro del giro."
		ko "   ⚠ Un giro che ha parlato col server ne lascia SEMPRE: questo"
		ko "     non e' uno zero, e' uno strumento che non vede."
		[ -s "$fuori.errori" ] && sed 's/^/            /' < "$fuori.errori"
		inf "marca: $(cat "$LAV/registro.marca" 2>/dev/null) byte · registro: \
$(stat -c %s "$LAV/registro.log" 2>/dev/null) byte"
		return 1
	fi
	inf "⭐ lo strumento vede: $n righe della tela nel giro"
	return 0
}

# ===========================================================================
# ⭐⭐ IL GIRO SANO, PRIMA DI TUTTI I GUASTI — e senza di lui il resto non prova
#     niente.  Rilievo della revisione avversariale, 21 agosto 2026:
#     *«Non c'e' NESSUN giro sano, in tutto il certificatore.»*
#
# ⛔ `fasi/06 §5.1`: il codice **sano** produce gia' 4 giri su 18 col desktop
#    non adattato e `NON_ORA` al fondo dei 3 s.  ⇒ La regola di G1
#    (`non_ora >= 6 and ms_mediano > 2500 and fotogrammi < 100`) puo' tornare
#    vera **sul sano**, sotto contesa GPU.  Senza un giro sano preso nella
#    STESSA ora e sotto lo STESSO carico, il certificatore certificherebbe il
#    carico credendo di certificare il guasto.
# ===========================================================================
SANO_AMB="$LAV/06-b35-ambiente-sano.json"
rm -f "$SANO_AMB"
log "IL GIRO SANO — il metro contro cui si leggono i cinque guasti"
bash "$T" spegni > /dev/null 2>&1
if ! D="$SANO/src" bash "$T" accendi > "$LAV/certifica-SANO-accendi.log" 2>&1; then
	ko "⛔ il server SANO non si accende: i guasti restano SENZA METRO"
	printf 'SANO NON-ACCENDE\n' >> "$ESITI"
else
	sleep 6
	D="$SANO/src" bash "$T" registro-da | sed 's/^/        /'
	US=$(giro "gSANO" "/srv/src/$(basename "$SANO")")
	inf "il client sano e' uscito con $US"
	cp -f "$LAV/registro.log" "$LAV/certifica-SANO-registro.log" 2>/dev/null
	# ⛔ Un giro sano che non ha misurato NON e' un metro: 2 = la stretta di
	#    mano non e' arrivata, 5 = «IL PALCO, NON IL PRODOTTO».  Usarlo come
	#    riferimento vorrebbe dire misurare i guasti contro un guasto.
	if [ "$US" = "2" ] || [ "$US" = "5" ]; then
		ko "⛔ il giro SANO e' uscito con $US: NON e' un metro, e non lo uso"
	elif leggi_registro "$SANO/src" "$LAV/certifica-SANO-tela.txt"; then
		NSs=$(grep -ac 'NON lo spedisco' "$LAV/certifica-SANO-tela.txt"); [ -n "$NSs" ] || NSs=0
		Ns=$(grep -ac 'TELA NUOVA DAL PALCO' "$LAV/certifica-SANO-tela.txt"); [ -n "$Ns" ] || Ns=0
		if python3 "$SANO/banchi/06-b35-regola.py" ambiente \
			"$LAV/06-b35-gSANO.json" "$Ns" "$NSs" > "$SANO_AMB" 2>/dev/null; then
			ok "metro sano: $(cat "$SANO_AMB")"
			printf 'SANO %s\n' "$(cat "$SANO_AMB")" >> "$ESITI"
		else
			ko "⛔ il giro sano non ha lasciato numeri leggibili"
			rm -f "$SANO_AMB"
		fi
	else
		ko "⛔ registro cieco sul giro SANO"
		rm -f "$SANO_AMB"
	fi
fi
bash "$T" spegni > /dev/null 2>&1
if [ ! -s "$SANO_AMB" ]; then
	ko "⚠ NESSUN METRO SANO: i cinque casi si misurano lo stesso, ma ogni"
	ko "  «ATTESO-CONFERMATO» qui sotto va letto come «non messo a confronto»."
	printf 'SANO MANCANTE — nessun confronto possibile\n' >> "$ESITI"
fi

for Q in $QUALI; do
	log "GUASTO $Q"
	# ⛔ Si riparte SEMPRE dai file sani: un guasto ritirato male lascerebbe
	#    due guasti addosso al successivo, e l'atteso non varrebbe piu'.
	cp -f "$SANO/src/figlio.c" "$SANO/src/cattura.c" "$GUASTO/src/" || {
		ko "⛔ non ho rimesso i file sani"; continue; }
	python3 "$G" innesta "$Q" "$GUASTO/src" | sed 's/^/        /' || {
		ko "⛔ l'innesto non e' riuscito: il caso non si misura"; continue; }
	python3 "$G" elenca | grep -A2 "^$Q " | sed 's/^/        /'

	# ⛔⛔ SI GUARDA L'ESITO DEL COSTRUTTORE, NON LA PRESENZA DEL BINARIO —
	#     rilievo della revisione avversariale, 21 agosto 2026.
	#     `$GUASTO` nasce da un `cp -a` fatto **una volta sola**, e si porta
	#     dentro il binario del giro precedente: `[ -x .../remotix ]` diceva
	#     «si'» anche quando la compilazione era fallita.  ⇒ Il giro misurava
	#     **codice non guasto**, e per G4 — che ha l'atteso VERDE — usciva un
	#     `ATTESO-CONFERMATO` senza che il guasto fosse mai stato dentro.
	#     ⚠ E' l'idioma che `06-b33-certifica.sh:144-146` gia' condannava per
	#     esteso: *«un binario di ieri risponde si' a esiste? come uno di
	#     adesso»*.
	# ⇒ Tre difese, e la prima da sola non basterebbe:
	#    1. il binario si TOGLIE prima di costruire;
	#    2. si guarda lo STATO D'USCITA di `costruisci.sh`;
	#    3. si guarda che il binario sia PIU' NUOVO del sorgente guasto.
	rm -f "$GUASTO/src/remotix"
	if ! bash /media/REMOTIX/enter.sh --root "bash $C_GUASTO/src/costruisci.sh" \
		> "$LAV/certifica-$Q-costruisci.log" 2>&1; then
		ko "⛔ $Q non compila (costruisci.sh e' uscito rosso):"
		tail -5 "$LAV/certifica-$Q-costruisci.log" | sed 's/^/        /'
		printf '%s NON-COMPILA\n' "$Q" >> "$ESITI"
		continue
	fi
	if [ ! -x "$GUASTO/src/remotix" ]; then
		ko "⛔ $Q: costruisci.sh e' uscito verde ma il binario NON C'E'"
		printf '%s NON-COMPILA (binario assente)\n' "$Q" >> "$ESITI"
		continue
	fi
	if [ "$GUASTO/src/remotix" -ot "$GUASTO/src/figlio.c" ] ||
	   [ "$GUASTO/src/remotix" -ot "$GUASTO/src/cattura.c" ]; then
		ko "⛔ $Q: il binario e' PIU' VECCHIO del sorgente guasto ⇒ il guasto"
		ko "   non e' dentro, e il giro misurerebbe il codice di prima"
		printf '%s BINARIO-VECCHIO\n' "$Q" >> "$ESITI"
		continue
	fi
	# ⛔ Anche il binario APPENA COSTRUITO: `costruisci.sh` gira da root, e i
	#    modi glieli da' l'umask di questo processo.
	chmod -R a+rX "$GUASTO"
	ok "compilato, ed eseguibile dall'utente del banco"
	if ! setpriv --reuid=1008 --regid=1008 --clear-groups \
	     test -x "$GUASTO/src/remotix"; then
		# ⭐ SI VERIFICA invece di sperare (forma E1), e si verifica DALL'UTENTE
		#    CHE DEVE ESEGUIRLO: `test -x` da root dice sempre di si'.
		ko "⛔ $Q: l'uid 1008 NON puo' eseguire $GUASTO/src/remotix"
		printf '%s NON-ESEGUIBILE\n' "$Q" >> "$ESITI"
		continue
	fi

	bash "$T" spegni > /dev/null 2>&1
	# ⛔⛔ LA MARCA SI PRENDE **DOPO** L'ACCENSIONE, e prima era il contrario
	#     — rilievo della revisione avversariale, 21 agosto 2026.
	#     `registro-da` salvava `stat -c %s` del registro, e la riga dopo
	#     `accendi` faceva `: > "$LOG"`: il registro ripartiva da zero mentre
	#     la marca restava quella di prima.  ⇒ `registro-tela` faceva
	#     `tail -c "+$((M+1))"` su un file piu' corto della marca e non
	#     prendeva **niente**.
	#     ⛔ E le due conseguenze erano proprio i due guasti del mandato:
	#       · `tela_nuova_dal_palco == 0` — terza clausola di **G3** — era vera
	#         GRATIS, cioe' senza guardare;
	#       · `non_spediti > 0` di **G5** era IRRAGGIUNGIBILE, e G5 finiva in
	#         `NON-MISURATO: il compositore non ha consegnato` — cioe' proprio
	#         l'attribuzione sbagliata che il riquadro qui sotto dichiara di
	#         aver curato.
	#     ⚠ `06-b35-lancia.sh` aveva l'ordine giusto: il difetto stava **solo**
	#       qui, ed era qui dal primo giorno del banco.
	if ! D="$GUASTO/src" bash "$T" accendi > "$LAV/certifica-$Q-accendi.log" 2>&1; then
		ko "⛔ il server guasto non si accende"
		printf '%s NON-ACCENDE\n' "$Q" >> "$ESITI"
		continue
	fi
	# ⛔⭐ E SI ASPETTA DAVVERO CHE IL SERVER SIA PRONTO — difetto del BANCO
	#     trovato misurando, 16 agosto 2026: con `sleep 1` tutti e cinque i
	#     guasti finivano con `CONGEDO 0x10` sull'`AMMESSO`, cioe' **la stretta
	#     di mano non arrivava a SESSIONE** e non si misurava niente.  ⚠ Il banco
	#     avrebbe scritto cinque «ATTESO-SMENTITO» accusando il proprio ritardo
	#     di accensione: e' `CODER.md` §2.3 — *una prova che boccia il codice
	#     giusto costa quanto una che promuove quello sbagliato*.
	sleep 6
	# ⭐ Adesso, a server acceso e pronto: da qui in poi e' il giro che misuro.
	D="$GUASTO/src" bash "$T" registro-da | sed 's/^/        /'
	U=$(giro "g$Q")
	if [ "$U" = "2" ]; then
		# ⚠ Il ritentativo si DICHIARA, e uno solo: se il caso si misura solo
		#   al secondo colpo, chi legge deve saperlo.
		inf "⚠ prima uscita 2 (stretta di mano): RITENTO una volta"
		sleep 6
		U=$(giro "g$Q")
	fi
	inf "il client e' uscito con $U"
	# ⭐ Il registro del giro si TIENE, guasto per guasto: `accendi` lo azzera, e
	#    senza questa copia la diagnosi di un caso «non misurato» sarebbe
	#    impossibile — si guarderebbe il registro di un altro giro.
	cp -f "$LAV/registro.log" "$LAV/certifica-$Q-registro.log" 2>/dev/null
	if [ "$U" = "2" ]; then
		ko "⚠ $Q NON MISURATO: la stretta di mano non e' arrivata a SESSIONE"
		printf '%s NON-MISURATO (stretta di mano)\n' "$Q" >> "$ESITI"
		bash "$T" spegni > /dev/null 2>&1
		continue
	fi

	# ⛔⛔⭐ E «ZERO FOTOGRAMMI AL CLIENT» NON E' «IL PALCO NON CONSEGNA» —
	#       limite della guardia trovato misurando G5, 16 agosto 2026.
	#
	# Il client vede una cosa sola: che non gli arriva niente.  ⛔ Ma «il
	# compositore tace» e «il prodotto li scarta tutti perche' dichiarano una
	# misura sbagliata» gli arrivano **identici**, e la guardia «IL PALCO, NON
	# IL PRODOTTO» attribuiva al compositore una colpa del prodotto — cioe' il
	# rosso all'imputato sbagliato, al contrario.
	# ⇒ La distinzione sta nel REGISTRO, che il client non puo' leggere (gira
	#   nel contenitore, il registro e' di root): la fa qui il certificatore.
	if ! leggi_registro "$GUASTO/src" "$LAV/certifica-$Q-tela.txt"; then
		ko "⛔ $Q NON MISURATO: lo STRUMENTO che conta le righe del registro"
		ko "   e' cieco (vedi sopra).  ⚠ Un «0» adesso sarebbe lo zero di"
		ko "   `LEZIONI.md` §1.9: vuoto e giusto con la stessa faccia — e"
		ko "   proprio «0» e' quel che la regola di G3 pretende."
		printf '%s NON-MISURATO (strumento cieco sul registro)\n' "$Q" >> "$ESITI"
		bash "$T" spegni > /dev/null 2>&1
		continue
	fi
	NS=$(grep -ac 'NON lo spedisco' "$LAV/certifica-$Q-tela.txt"); [ -n "$NS" ] || NS=0
	if [ "$U" = "5" ] && [ "$NS" -eq 0 ]; then
		ko "⚠ $Q NON MISURATO: il compositore non ha consegnato (e il registro"
		ko "   lo conferma: ZERO fotogrammi scartati per misura)"
		printf '%s NON-MISURATO\n' "$Q" >> "$ESITI"
	else
		[ "$U" = "5" ] && inf "⭐ uscita 5, ma il registro dice $NS fotogrammi \
scartati per misura: il palco CONSEGNAVA, e il caso SI MISURA"
		# ⭐ Il verdetto lo legge il JSON del client, e le righe del registro
		#    le conta qui: due fonti, perche' «il palco non ha obbedito» e
		#    «non gli e' stato chiesto» si distinguono solo dal registro.
		# ⛔ `grep -c` stampa 0 ED ESCE 1: un `|| echo 0` in coda aggiungerebbe
		#    un SECONDO zero, e il conto diventerebbe la stringa «0\n0».  ⚠ E'
		#    la forma di `LEZIONI.md` §1.9 punto 1 — lo zero e il fallimento
		#    hanno lo stesso aspetto — dentro l'attrezzo che serve a contarli.
		# ⭐ E il file lo ha gia' prodotto `leggi_registro`, che si e' fatto
		#    carico del controllo positivo: qui si conta e basta.
		N=$(grep -ac 'TELA NUOVA DAL PALCO' "$LAV/certifica-$Q-tela.txt")
		[ -n "$N" ] || N=0
		# ⭐ I sei numeri e il giudizio stanno in `06-b35-regola.py`, separati
		#    apposta: cosi' la regola si applica DUE volte — al guasto e al
		#    giro SANO — e un caso che non distingue lo dice.
		AMB="$LAV/06-b35-ambiente-$Q.json"
		if ! python3 "$SANO/banchi/06-b35-regola.py" ambiente \
			"$LAV/06-b35-g$Q.json" "$N" "$NS" > "$AMB" 2> "$AMB.errori"; then
			ko "⛔ $Q SENZA-JSON: $(head -3 "$AMB.errori" | tr '\n' ' ')"
			printf '%s SENZA-JSON\n' "$Q" >> "$ESITI"
			bash "$T" spegni > /dev/null 2>&1
			continue
		fi
		if [ -s "$SANO_AMB" ]; then
			python3 "$SANO/banchi/06-b35-regola.py" giudica \
				"$AMB" "$Q" "$G" "$SANO_AMB" >> "$ESITI"
		else
			python3 "$SANO/banchi/06-b35-regola.py" giudica \
				"$AMB" "$Q" "$G" >> "$ESITI"
		fi
		tail -1 "$ESITI" | sed 's/^/        /'
	fi
	bash "$T" spegni > /dev/null 2>&1
done

log "GLI ESITI"
cat "$ESITI" | sed 's/^/    /'
V=$(grep -c ' ATTESO-CONFERMATO' "$ESITI"); [ -n "$V" ] || V=0
N=$(grep -c ' ATTESO-SMENTITO' "$ESITI"); [ -n "$N" ] || N=0
# ⛔ Il terzo conto, che prima non esisteva: i casi in cui la regola torna vera
#    ANCHE sul codice sano.  ⚠ Non sono ne' verdi ne' rossi: NON DISTINGUONO,
#    e sommarli ai confermati sarebbe la bugia peggiore di questo banco.
ND=$(grep -c ' NON-DISCRIMINANTE' "$ESITI"); [ -n "$ND" ] || ND=0
# ⚠ E il denominatore e' il numero di GUASTI chiesti, non le righe del file:
#   le righe portano dentro anche il metro sano e le diagnosi.
QN=0; for _q in $QUALI; do QN=$((QN + 1)); done
printf '\n    attesi CONFERMATI: %s · SMENTITI: %s · ⛔ NON DISCRIMINANTI: %s   (su %s guasti chiesti)\n' \
	"$V" "$N" "$ND" "$QN"
if [ "$ND" -gt 0 ]; then
	ko "⛔ $ND caso/i torna vero anche sul codice SANO misurato nella stessa"
	ko "   ora: quei casi NON certificano niente, e vanno letti come tali."
fi
if [ ! -s "$SANO_AMB" ]; then
	ko "⛔ E non c'e' stato metro sano: nessuno dei «CONFERMATI» qui sopra e'"
	ko "   stato messo a confronto con il codice sano."
fi
# ⚠ E «non visto» non e' sempre un difetto del banco: G4 ha l'atteso VERDE, e
#   la sua riga qui sopra e' la dichiarazione di quel che questo banco NON copre.
inf "⚠ G4 ha l'atteso VERDE per costruzione: leggi il suo «atteso» in 06-b35-guasti.py"
inf "esiti: $ESITI"

log "Rimetto in piedi il server SANO"
D="$SANO/src" bash "$T" accendi | tail -2
exit 0
