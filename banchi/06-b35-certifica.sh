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

giro() {   # $1 = etichetta
	bash /media/REMOTIX/enter.sh \
		"python3 $C_GUASTO/banchi/06-b35-tela.py --porta $PORTA \
		 --utente $UTENTE --parola-file $C_LAV/parola-certifica --lavoro $C_LAV \
		 --giro dieci --coda 3 --etichetta $1 \
		 --scena 'controllo positivo: gnome-terminal a 50 ms'" \
		> "$LAV/certifica-$1.txt" 2>&1
	echo $?
}

for Q in $QUALI; do
	log "GUASTO $Q"
	# ⛔ Si riparte SEMPRE dai file sani: un guasto ritirato male lascerebbe
	#    due guasti addosso al successivo, e l'atteso non varrebbe piu'.
	cp -f "$SANO/src/figlio.c" "$SANO/src/cattura.c" "$GUASTO/src/" || {
		ko "⛔ non ho rimesso i file sani"; continue; }
	python3 "$G" innesta "$Q" "$GUASTO/src" | sed 's/^/        /' || {
		ko "⛔ l'innesto non e' riuscito: il caso non si misura"; continue; }
	python3 "$G" elenca | grep -A2 "^$Q " | sed 's/^/        /'

	bash /media/REMOTIX/enter.sh --root "bash $C_GUASTO/src/costruisci.sh" \
		> "$LAV/certifica-$Q-costruisci.log" 2>&1
	if [ ! -x "$GUASTO/src/remotix" ]; then
		ko "⛔ $Q non compila: vedi $LAV/certifica-$Q-costruisci.log"
		printf '%s NON-COMPILA\n' "$Q" >> "$ESITI"
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
	D="$GUASTO/src" bash "$T" registro-da > /dev/null
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
	NS=$(D="$GUASTO/src" bash "$T" registro-tela 2>/dev/null 		| grep -ac 'NON lo spedisco'); [ -n "$NS" ] || NS=0
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
		N=$(D="$GUASTO/src" bash "$T" registro-tela 2>/dev/null \
			| grep -ac 'TELA NUOVA DAL PALCO')
		# ⛔ `grep -c` stampa 0 ED ESCE 1: un `|| echo 0` in coda aggiungerebbe
		#    un SECONDO zero, e il conto diventerebbe la stringa «0\n0».  ⚠ E'
		#    la forma di `LEZIONI.md` §1.9 punto 1 — lo zero e il fallimento
		#    hanno lo stesso aspetto — dentro l'attrezzo che serve a contarli.
		[ -n "$N" ] || N=0
		python3 - "$LAV/06-b35-g$Q.json" "$Q" "$N" "$G" "$NS" >> "$ESITI" <<-'PY'
		import json, sys, statistics, importlib.util, os
		p, q, n_palco, gpath = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
		s = importlib.util.spec_from_file_location("g", gpath)
		m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
		try:
		    d = json.load(open(p))
		except Exception as e:
		    print(f"{q} SENZA-JSON ({e})"); raise SystemExit
		tele = [v for v in d["controllo_dopo_sessione"] if v["tipo"] == "TELA"]
		adattate = sum(1 for v in tele if v["esito"] == "ADATTATA")
		non_ora = sum(1 for v in tele if v["motivo"] == "NON_ORA")
		msl = [t["ms"] for t in d["tentativi"] if t.get("ms") is not None]
		ms_mediano = statistics.median(msl) if msl else -1
		# ⛔ «fotogrammi» sono quelli COMPLETI arrivati al client: uno
		#    spedito e non completato non e' un pixel.
		amb = {"adattate": adattate, "non_ora": non_ora,
		       "ms_mediano": ms_mediano, "fotogrammi": d["fotogrammi_totali"],
		       "tela_nuova_dal_palco": n_palco,
		       "non_spediti": int(sys.argv[5])}
		reg = m.GUASTI[q]["regola"]
		try:
		    visto = bool(eval(reg, {"__builtins__": {}}, amb))
		except Exception as e:
		    print(f"{q} REGOLA-ROTTA {e}"); raise SystemExit
		# ⛔ «CONFERMATO» vuol dire che l'ATTESO DICHIARATO PRIMA si e'
		#    avverato — non «e' diventato rosso»: l'atteso di G4 e' VERDE, e
		#    chiamarlo «visto» direbbe il falso su meta' dei casi.
		print(f"{q} {'ATTESO-CONFERMATO' if visto else 'ATTESO-SMENTITO'} "
		      f"adattate={adattate} non_ora={non_ora} "
		      f"ms_mediano={ms_mediano} fotogrammi={d['fotogrammi_totali']} "
		      f"tela_nuova_dal_palco={n_palco} non_spediti={sys.argv[5]}  "
		      f"[regola: {reg}]")
		PY
		tail -1 "$ESITI" | sed 's/^/        /'
	fi
	bash "$T" spegni > /dev/null 2>&1
done

log "GLI ESITI"
cat "$ESITI" | sed 's/^/    /'
V=$(grep -c ' ATTESO-CONFERMATO' "$ESITI" 2>/dev/null); [ -n "$V" ] || V=0
N=$(grep -c ' ATTESO-SMENTITO' "$ESITI" 2>/dev/null); [ -n "$N" ] || N=0
printf '\n    attesi CONFERMATI: %s · SMENTITI: %s (su %s guasti)\n' "$V" "$N" "$(wc -l < "$ESITI")"
# ⚠ E «non visto» non e' sempre un difetto del banco: G4 ha l'atteso VERDE, e
#   la sua riga qui sopra e' la dichiarazione di quel che questo banco NON copre.
inf "⚠ G4 ha l'atteso VERDE per costruzione: leggi il suo «atteso» in 06-b35-guasti.py"
inf "esiti: $ESITI"

log "Rimetto in piedi il server SANO"
D="$SANO/src" bash "$T" accendi | tail -2
exit 0
