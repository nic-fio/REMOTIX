#!/bin/bash
#
# 02-giudizio-telefono.sh — F2.6 (b): LA SONDA SUL DISPOSITIVO VERO.
#                           `PIANO.md` §1.2 domanda S2, e fase 2.
#
#   bash banchi/02-giudizio-telefono.sh serve      accende il sito e stampa l'indirizzo
#   bash banchi/02-giudizio-telefono.sh flusso     ⛔ costruisce il flusso di un giro NUOVO
#                                                  sul raccoglitore GIA' acceso
#   bash banchi/02-giudizio-telefono.sh procedura  ⛔ che cosa serve dall'utente
#   bash banchi/02-giudizio-telefono.sh controllo  ⛔ il canale di lettura funziona?
#   bash banchi/02-giudizio-telefono.sh analizza   legge il registro e giudica i pixel
#   bash banchi/02-giudizio-telefono.sh certifica  ⛔ il giro dal PORTATILE: dev'essere
#                                                  RIFIUTATO, e tutto il resto deve girare
#   bash banchi/02-giudizio-telefono.sh spegni
#
# ⚠ GIRA SU CHUWI, sulla porta **7516**.  ⛔ Non tocca NIC-OS: non accende e non
#   spegne niente la' sopra — la 7448 e la 7501 stanno accese apposta.  Il sito
#   di S1b sulla 7452 **non si riusa e non si disturba**: e' un orologio da
#   sette giorni con un certificato che non si rigenera per nessun motivo.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE, E QUALE MISURA SBAGLIATA IMPEDISCE
#
# La misura sbagliata, e sarebbe facilissima da fare, e':
#
#     «ho aperto la pagina sul Chrome del portatile, decodifica HEVC Main10 in
#      hardware e i pixel coincidono ⇒ S2 e' chiusa»
#
# ⛔ Non dice **niente** del telefono.  E' la forma d'errore **E10** — una
#    prova verde sul client sbagliato — con il travestimento nuovo che
#    `DECISIONI.md` §5-bis.0-ter le ha dato il 9 agosto 2026:
#
#      *«nessun numero si dichiara su un browser che non sia quello del
#        dispositivo vero»*
#
#    Su Android il decodificatore vive dietro **MediaCodec**, che e'
#    precisamente la cosa che rende inutili i segnali JS: quel che si misura
#    qui **non esiste altrove**.
#
# ---------------------------------------------------------------------------
# ⛔ LE DUE DOMANDE, E LA SECONDA HA UN INDIZIO CONTRARIO GIA' RACCOLTO
#
#   1. il browser del telefono decodifica **HEVC Main10 in hardware**?
#      `[S]` Chrome lo documenta dalla 108 — ⛔ ma quel `[S]` riguarda il
#      **supporto in WebCodecs**, non l'hardware.  Nel browser **il nome del
#      decodificatore non c'e'**: la prova e' indiretta e va costruita col
#      caso opposto scritto prima (`LEZIONI.md` §1.11).  Il caso opposto sta
#      scritto per esteso nell'intestazione di `02-giudizio-pagina.html`.
#
#   2. ⛔ **e restituisce davvero 10 bit?**  `[?]`  E qui c'e' un'indicazione
#      **contraria**: `DECISIONI.md` §2.3-bis — la documentazione di mpv
#      riporta che sul percorso `mediacodec` di Android il supporto a 10 bit e'
#      **limitato e l'uscita torna a 8 bit**; mpv-android #462 mostra HEVC 10
#      bit che escono **verdi e distorti** su Pixel 6.
#      ⚠ Non e' una prova (e' il percorso di mpv, non il nostro) **ma non si
#        tace**: e' la prima cosa che punta contro il desiderato di
#        `SPECIFICHE.md` §3.1, e arriva dal lato dove non abbiamo margine.
#
#   ⚠ **E se la risposta fosse no, non e' un muro** (`DECISIONI.md` §2.7): il
#     massimo lo offre il server, l'altezza la mette il client.  Un dispositivo
#     che decodifica in software, o che tronca a 8 bit, e' un fatto da
#     **misurare e dichiarare** — ⛔ ma dichiarato va dichiarato: un ripiego
#     silenzioso resta vietato anche quando la colpa e' di qualcun altro.
#
# ---------------------------------------------------------------------------
# ⛔⭐ IL CONTROLLO POSITIVO DEL CANALE DI LETTURA — il piu' importante
#
# Copiato dal controllo n. 4 di `01-s1b-eccezione.sh`, nato dal rilievo A27,
# che e' il piu' grave che quel file abbia avuto.  Il buco che chiude:
#
#   `analizza` legge il registro del raccoglitore.  Se il registro non c'e',
#   o e' stato ripulito, o il raccoglitore non scrive, **la risposta e' «il
#   telefono non ha risposto»** — che e' la stessa frase che si direbbe se il
#   telefono avesse davvero fallito.  ⛔ Tre cause, un solo silenzio.
#
# ⭐ La cura: prima di ogni verdetto lo script **si spedisce da solo** un
#    gettone con `POST /prova` e poi lo rilegge dal registro.  Se non torna,
#    il canale e' rotto e **nessun verdetto si da'**.
#    ⚠ E si dichiara che cosa questo controllo NON prova: non prova che un
#      BROWSER arrivi alla pagina.  Prova che il server scrive, che il file si
#      legge e che il `grep` trova — cioe' i tre pezzi su cui il verdetto
#      poggia e su cui nessun altro controllo guardava.
#
# ---------------------------------------------------------------------------
# ⛔⛔ I DUE DIFETTI CURATI LA SERA DEL 12 AGOSTO 2026 — e l'utente li ha
#     scoperti prima di me, spendendoci dieci minuti col telefono in mano
#
# **D16 — `serve` accendeva il sito SENZA il flusso da decodificare.**
#   La pagina chiedeva `/flusso-<giro>.json`, il server rispondeva **404**, e
#   gli esiti «negativi» che l'utente ha visto non erano il telefono che
#   falliva: era **la sonda che non aveva niente in mano**.
#   ⛔ E' la forma **E8**: «il dispositivo non e' arrivato» e «il dispositivo
#      e' arrivato e non aveva niente da decodificare» avevano la stessa
#      faccia.  ⛔ Ed e' il peggiore dei due, perche' con un riconoscimento
#      del dispositivo funzionante avrebbe prodotto **un verdetto falso** —
#      «il telefono non decodifica» — che nessuno avrebbe messo in dubbio.
#   ⇒ LA CURA, in tre pezzi:
#     1. `serve` **costruisce** il flusso (`02-giudizio-flusso.py`, quattro
#        sequenze gia' certificate da F2.5: HEVC e AV1, 8 e 10 bit) **prima**
#        di accendere qualunque cosa, e se non ci riesce **non accende**;
#     2. `serve` **rilegge il flusso DAL SERVER**, con `curl`, sullo stesso
#        indirizzo che chiedera' il telefono: il 404 era HTTP, e un controllo
#        fatto sul disco non l'avrebbe visto;
#     3. la pagina se ne accorge **da sola** e spedisce `FLUSSO_ASSENTE`
#        invece di un esito che somiglia a una misura.
#
# **D17 — il riconoscimento del dispositivo era sulla STRINGA del browser.**
#   Chrome per Android in **Samsung DeX** manda
#     `Mozilla/5.0 (X11; Linux x86_64) … Chrome/150.0.0.0 Safari/537.36`
#   che dalla sola stringa e' **indistinguibile da un desktop**.  Il banco ha
#   detto «NESSUNA riga viene da un dispositivo mobile» **mentre il telefono
#   era li'** — l'indirizzo era `192.168.0.24`, ne' il portatile (`.3`) ne' il
#   server (`.2`), e la versione era 150 contro la 151 del portatile.
#   ⇒ La cura sta in `02-giudizio-dispositivo.py`, su **due assi**: la
#     PROVENIENZA (che il browser non puo' scrivere) e la NATURA (che il
#     browser dichiara).  ⭐ E DeX e' **un caso a se'**, che il registro deve
#     poter DIRE invece di doverlo scegliere fra «telefono» e «desktop».
#   ⛔ La difesa E10 non si e' indebolita: la provenienza ha diritto di
#      **veto**, e il caso `portatile-travestito` lo misura.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-7516}
CERTDIR=${CERTDIR:-$HOME/.remotix-f26}
REGISTRO=$QUI/02-giudizio-sonda.jsonl
PIDFILE=$CERTDIR/raccoglitore.pid
GIRO=${GIRO:-$(date +%Y%m%d-%H%M)}

VERDE='\033[1;32m'; ROSSO='\033[1;31m'; GIALLO='\033[1;33m'; GRIGIO='\033[0m'
log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf "    ${VERDE}OK${GRIGIO}  %s\n" "$*"; }
ko()   { printf "    ${ROSSO}NO${GRIGIO}  %s\n" "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

indirizzo()
{
	# ⛔ NON `localhost`: il telefono non ci arriva, e Chrome ha una corsia
	#    riservata per localhost dove la misura non rappresenta niente
	#    (S1 §4.5.3).  Si prende l'indirizzo privato di QUESTA macchina.
	ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1 | head -1
}

certificato()
{
	mkdir -p "$CERTDIR"
	if [ -s "$CERTDIR/cert.pem" ] && [ -s "$CERTDIR/chiave.pem" ]; then
		inf "certificato gia' presente in $CERTDIR"
		return 0
	fi
	local ind
	ind=$(indirizzo)
	openssl req -x509 -newkey rsa:2048 -nodes -days 90 \
		-keyout "$CERTDIR/chiave.pem" -out "$CERTDIR/cert.pem" \
		-subj "/CN=$ind" -addext "subjectAltName=IP:$ind"
	if [ $? -ne 0 ]; then
		ko "il certificato non e' stato creato"
		return 2
	fi
	ok "certificato nuovo per $ind, 90 giorni, in $CERTDIR"
	inf "⛔ vive FUORI dal deposito apposta: non e' roba da git, e non e'"
	inf "   il certificato di S1b — quello non si tocca"
}

case "${1:-procedura}" in

serve)
	log "1. Il certificato"
	certificato || exit 2

	log "2. ⛔ IL FLUSSO DA DECODIFICARE — o non si serve (D16)"
	if ! python3 "$QUI/02-giudizio-flusso.py" "$GIRO"; then
		ko "il flusso del giro $GIRO NON si costruisce."
		ko "   ⛔ E allora NON accendo niente: un sito acceso senza flusso"
		ko "      fa dire «il telefono non decodifica» a un telefono che non"
		ko "      ha ricevuto niente — ed e' un [M] falso contro un componente"
		ko "      innocente.  E' il difetto D16, pagato stasera."
		exit 2
	fi

	log "3. Il raccoglitore sulla $PORTA"
	if [ -s "$PIDFILE" ] && [ -d "/proc/$(cat "$PIDFILE")" ]; then
		ok "gia' acceso (pid $(cat "$PIDFILE"))"
	else
		python3 -u "$QUI/02-giudizio-raccogli.py" "$PORTA" \
			"$CERTDIR/cert.pem" "$CERTDIR/chiave.pem" "$QUI" \
			> "$CERTDIR/raccoglitore.log" 2>&1 &
		echo $! > "$PIDFILE"
		sleep 1
		if [ ! -d "/proc/$(cat "$PIDFILE")" ]; then
			ko "il raccoglitore non e' partito.  Il suo registro:"
			sed 's/^/        /' "$CERTDIR/raccoglitore.log"
			exit 2
		fi
		ok "acceso (pid $(cat "$PIDFILE")) — registro in $CERTDIR/raccoglitore.log"
	fi

	log "4. ⛔ IL CONTROLLO CHE MANCAVA: il flusso si scarica DAL SERVER?"
	inf "il 404 di stasera era HTTP: un controllo fatto sul disco non l'avrebbe"
	inf "visto.  Qui si chiede lo stesso identico indirizzo che chiede il telefono."
	for f in "02-giudizio-pagina.html" "flusso-$GIRO.json"; do
		C=$(curl -sk -o /dev/null -w '%{http_code}' \
			"https://127.0.0.1:$PORTA/$f")
		if [ "$C" = "200" ]; then
			ok "GET /$f → $C"
		else
			ko "GET /$f → $C"
			ko "   ⛔ Il sito e' acceso ma NON serve quel che la pagina chiede."
			ko "      Non do' l'indirizzo: un giro fatto cosi' produce esiti che"
			ko "      SEMBRANO una misura del dispositivo e non lo sono."
			exit 2
		fi
	done

	log "5. L'indirizzo da aprire SUL TELEFONO"
	printf '\n        https://%s:%s/02-giudizio-pagina.html?giro=%s\n\n' \
		"$(indirizzo)" "$PORTA" "$GIRO"
	inf "⚠ comparira' l'avviso del certificato: si accetta UNA volta."
	inf "  E' esattamente il meccanismo che S1b sta misurando sulla 7452."
	inf "⚠ ⛔ e il giro sta NELL'INDIRIZZO: aprire un indirizzo con un giro"
	inf "  vecchio ridarebbe 404 sul flusso.  Si copia questa riga com'e'."
	;;

flusso)
	# ⛔ Serve a una cosa sola, e importante: dare all'utente un indirizzo
	#    NUOVO **senza spegnere e riaccendere** il raccoglitore.  L'eccezione
	#    del certificato l'ha gia' accettata, e farla ricomparire e' un modo
	#    di spendere il suo tempo per niente.
	log "Il flusso per il giro $GIRO, sul raccoglitore gia' acceso"
	python3 "$QUI/02-giudizio-flusso.py" "$GIRO" || exit 2
	C=$(curl -sk -o /dev/null -w '%{http_code}' \
		"https://127.0.0.1:$PORTA/flusso-$GIRO.json")
	if [ "$C" != "200" ]; then
		ko "GET /flusso-$GIRO.json → $C: il raccoglitore non e' acceso, o"
		ko "   non serve da questa cartella.  ⛔ Nessun indirizzo si da'."
		exit 2
	fi
	ok "il flusso si scarica dal server (HTTP $C)"
	printf '\n        https://%s:%s/02-giudizio-pagina.html?giro=%s\n\n' \
		"$(indirizzo)" "$PORTA" "$GIRO"
	;;

controllo)
	log "⛔ IL CONTROLLO POSITIVO DEL CANALE DI LETTURA"
	inf "senza questo, «il telefono non ha risposto» e «il registro non si"
	inf "legge» sono la stessa frase — ed e' il buco A27 di S1b"
	G="gettone-$$-$(date +%s)"
	curl -sk -X POST --data "{\"gettone\":\"$G\"}" \
		"https://127.0.0.1:$PORTA/prova"
	st=$?
	if [ $st -ne 0 ]; then
		ko "curl non ha potuto spedire (stato $st): il raccoglitore non risponde."
		ko "   ⛔ Nessun verdetto si da'."
		exit 2
	fi
	sleep 1
	if [ ! -f "$REGISTRO" ]; then
		ko "il registro $REGISTRO NON ESISTE dopo una scrittura riuscita."
		ko "   ⛔ Il canale e' rotto: nessun verdetto."
		exit 2
	fi
	if grep -q "$G" "$REGISTRO"; then
		ok "il gettone spedito e' tornato dal registro: il canale scrive e legge"
		inf "⚠ e questo NON prova che un browser arrivi alla pagina: prova che il"
		inf "  server scrive, che il file si legge e che la ricerca trova"
		exit 0
	fi
	ko "il gettone NON e' tornato dal registro."
	ko "   ⛔ Il canale di lettura e' rotto.  Nessun verdetto si da'."
	exit 2
	;;

analizza)
	log "0. Prima di ogni verdetto: il canale"
	bash "$0" controllo || { ko "canale rotto: mi fermo"; exit 2; }

	log "1. ⛔ IL RICONOSCIMENTO SI CERTIFICA PRIMA DI ESSERE USATO"
	inf "sette casi, l'atteso scritto prima — e i due che contano sono DeX"
	inf "ACCETTATO e portatile RIFIUTATO.  Se questi non passano, il verdetto"
	inf "sul registro non vale niente."
	if ! python3 "$QUI/02-giudizio-dispositivo.py" --certifica >/dev/null; then
		ko "il riconoscimento non fa quel che ha dichiarato.  ⛔ Nessun verdetto."
		python3 "$QUI/02-giudizio-dispositivo.py" --certifica
		exit 2
	fi
	ok "sette casi su sette"

	log "2. ⛔ D16 — il flusso gliel'abbiamo DATO, o no?"
	inf "«non ha decodificato» e «non aveva niente da decodificare» sono due"
	inf "verdetti diversi, e prima di stasera avevano la stessa faccia (E8)."
	python3 - "$REGISTRO" <<'PY'
import json, sys
righe = []
for r in open(sys.argv[1], encoding="utf-8"):
    r = r.strip()
    if not r:
        continue
    try:
        righe.append(json.loads(r))
    except Exception:
        pass
flussi = [r for r in righe if r.get("tipo") == "richiesta"
          and "flusso-" in (r.get("percorso") or "")]
assenti = [r for r in righe if (r.get("dati") or {}).get("tipo") == "FLUSSO_ASSENTE"]
if not flussi:
    print("    \033[1;33m??\033[0m  nessuna richiesta del flusso nel registro.")
    print("        ⚠ Se il giro e' di PRIMA di stasera, il raccoglitore non")
    print("          registrava le letture: e' un buco del banco, non del")
    print("          dispositivo.  Se e' di adesso, la pagina non ha premuto")
    print("          il bottone 2.")
    sys.exit(0)
serviti = [r for r in flussi if r.get("codice") == 200]
persi = [r for r in flussi if r.get("codice") != 200]
for r in persi:
    print("    \033[1;31mNO\033[0m  %s  %s → %d  ⛔ il dispositivo E' arrivato e"
          % (r.get("ip"), r.get("percorso"), r.get("codice")))
    print("        NON aveva niente da decodificare.  Qualunque esito negativo")
    print("        di quel giro NON e' una misura del dispositivo (D16).")
for r in serviti:
    print("    \033[1;32mOK\033[0m  %s  %s → 200, %d byte"
          % (r.get("ip"), r.get("percorso"), r.get("byte", 0)))
for r in assenti:
    d = r["dati"]
    print("    --  ⭐ la PAGINA se n'e' accorta da sola: %s (%s)"
          % (d.get("perche"), d.get("indirizzo")))
sys.exit(1 if persi and not serviti else 0)
PY
	[ $? -ne 0 ] && { ko "il flusso non e' stato servito: mi fermo qui"; exit 2; }

	log "3. Chi e' arrivato alla pagina — su DUE assi, non sullo user agent"
	if [ ! -s "$REGISTRO" ]; then
		ko "il registro e' vuoto.  ⛔ Ma il canale funziona (l'ho appena"
		ko "   provato): quindi «vuoto» qui vuol dire davvero «nessuno e'"
		ko "   arrivato», e non «non ho potuto guardare»."
		exit 2
	fi
	python3 "$QUI/02-giudizio-dispositivo.py" "$REGISTRO" ${GIRO_FILTRO:+--giro "$GIRO_FILTRO"}
	st=$?
	if [ $st -eq 3 ]; then
		ko "⛔ nessuna riga viene da un dispositivo ACCETTATO."
		ko "   ⚠ E leggi bene il verdetto qui sopra: «RIFIUTATO» e «SOSPESO»"
		ko "     sono due cose diverse, e nessuna delle due dice «il"
		ko "     dispositivo ha fallito»."
		exit 2
	fi
	[ $st -ne 0 ] && exit 2

	log "4. I pixel — ⛔ e qui si chiude la meta' (a) sul dispositivo VERO"
	# ⛔⭐ E NON SI PRENDE «IL PIU' RECENTE».  Prima di stasera qui c'era un
	#     `ls -t | head -1`: bastava un giro di certifica fatto sul PORTATILE
	#     per lasciare in cartella un `pagina-*.rgb24` piu' fresco di quello
	#     del telefono, e il metro avrebbe giudicato i pixel del portatile
	#     credendoli del dispositivo — la forma **E10** entrata dalla porta di
	#     servizio.  ⇒ Si prendono solo i file spediti da una riga il cui
	#     dispositivo e' stato **ACCETTATO**.
	PAG=$(python3 - "$REGISTRO" "$QUI" <<'PY'
import importlib.util
import json, os, sys
spec = importlib.util.spec_from_file_location(
    "disp", os.path.join(sys.argv[2], "02-giudizio-dispositivo.py"))
disp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(disp)
locali = disp.indirizzi_locali()
buoni = []
for r in open(sys.argv[1], encoding="utf-8"):
    r = r.strip()
    if not r:
        continue
    try:
        d = json.loads(r)
    except Exception:
        continue
    if d.get("tipo") != "pixel":
        continue
    if disp.giudica(d, locali)["verdetto"] != "ACCETTATO":
        continue
    p = os.path.join(sys.argv[2], d.get("nome", ""))
    if os.path.isfile(p):
        buoni.append((d.get("ora"), p))
buoni.sort()
for _o, p in buoni:
    print(p)
PY
)
	if [ -z "$PAG" ]; then
		ko "nessun file di pixel viene da un dispositivo ACCETTATO."
		ko "   ⛔ Con il canale sano e un dispositivo arrivato, questo vuol dire"
		ko "      che la rilettura della tela e' fallita sul dispositivo — che e'"
		ko "      un fatto da scrivere, non un silenzio."
		ko "   ⚠ E se in cartella ci sono dei pagina-*.rgb24, sono di un giro"
		ko "     fatto da QUESTA macchina: non si giudicano (forma E10)."
		exit 2
	fi
	printf '%s\n' "$PAG" | while read -r p; do
		inf "pixel accettati: $p ($(stat -c %s "$p") byte)"
	done
	PAG=$(printf '%s\n' "$PAG" | tail -1)
	inf "⇒ il giudizio si da' con:"
	inf "   bash banchi/02-giudizio-confronto.sh giudica --scena … \\"
	inf "        --cattura … --riferimento … --pagina $PAG \\"
	inf "        --colore … --riferimento-10 … --identita-pagina …"
	;;

certifica)
	# -------------------------------------------------------------------
	# ⛔ IL CASO OPPOSTO, GIRATO PER DAVVERO — `LEZIONI.md` §1.11
	#
	# La domanda: **che aspetto ha un giro fatto dal PORTATILE?**  Deve
	# essere **RIFIUTATO** — quella difesa (forma E10) e' il motivo per cui
	# questa sonda esiste, e curando D17 e' facilissimo aprirci un buco.
	#
	# ⭐ E la parte che vale il doppio: si deve far vedere che **fino a quel
	#    punto tutto il resto ha funzionato**.  Un «rifiutato» su una catena
	#    rotta e un «rifiutato» su una catena sana hanno la stessa faccia, e
	#    il primo non certifica niente.  ⇒ Prima si misura la catena (pagina
	#    servita, flusso servito, sequenze decodificate, pixel arrivati), e
	#    **solo dopo** si controlla che il verdetto sia RIFIUTATO.
	#
	# ⛔ PORTA 7536, NON la 7516: sulla 7516 c'e' il raccoglitore che serve
	#    all'utente, con l'eccezione del certificato gia' accettata sul suo
	#    telefono.  Spegnerlo per certificare il banco sarebbe far ripagare
	#    a lui il conto due volte.  E registro separato, per la stessa
	#    ragione: il giro del portatile non si mescola col suo.
	#
	# ⚠ E IN CHIARO SU 127.0.0.1, dichiarato: `http://127.0.0.1` e' un
	#   **contesto sicuro** per specifica, quindi WebCodecs e getImageData
	#   funzionano identici — e cosi' non si chiede ne' a Chrome ne' a
	#   Firefox di accettare un certificato che non e' loro.  ⛔ Dal telefono
	#   questa strada non esiste: li' l'HTTPS serve davvero.
	# -------------------------------------------------------------------
	PORTA_C=${PORTA_C:-7536}
	SCHERMO=${SCHERMO:-:10}
	REG_C=$QUI/02-giudizio-sonda-certifica.jsonl
	T=$(mktemp -d)
	PID_C=
	GIRI=()
	congedo() {
		[ -n "$PID_C" ] && { kill "$PID_C" 2>/dev/null; wait "$PID_C" 2>/dev/null; }
		rm -rf "$T"
	}
	trap congedo EXIT
	ESITO=0

	log "1. Il riconoscimento, sui sette casi scritti prima"
	python3 "$QUI/02-giudizio-dispositivo.py" --certifica || ESITO=1

	log "2. ⭐ LA PAGINA SI LEGGE? — il controllo che e' costato un giro"
	# ⛔ `[M]` 12 agosto 2026, primo giro di questa certifica: un carattere
	#    «⛔» usato come NOME DI CAMPO in un oggetto JavaScript e' un errore
	#    di sintassi, e un errore di sintassi ferma **tutto lo script**.  Il
	#    sintomo da fuori era identico a quello di D16: la pagina servita 200,
	#    nessuna richiesta del flusso, nessun esito.  ⇒ Prima di guidare un
	#    browser si chiede a un lettore di JavaScript se la pagina si legge:
	#    «lo script non parte» e «il dispositivo non decodifica» non devono
	#    piu' avere la stessa faccia.
	if command -v node >/dev/null; then
		python3 - "$QUI/02-giudizio-pagina.html" "$T/pagina.js" <<'PY'
import sys
testo = open(sys.argv[1], encoding="utf-8").read()
open(sys.argv[2], "w", encoding="utf-8").write(
    testo.split("<script>")[1].split("</script>")[0])
PY
		if node --check "$T/pagina.js"; then
			ok "il JavaScript della pagina si legge per intero"
		else
			ko "⛔ il JavaScript della pagina NON si legge: nessun browser"
			ko "   arriverebbe al primo bottone.  Mi fermo qui."
			exit 2
		fi
	else
		inf "⚠ node non c'e': non ho potuto rileggere la pagina, E LO DICO"
	fi

	log "3. Lo schermo — ⛔ e dev'essere quello VERO"
	inf "su uno schermo finto Chrome non ha GPU e ogni stringa HEVC viene"
	inf "rifiutata (F2.5 §1): li' il rosso su HEVC non direbbe niente."
	if ! env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO xdpyinfo >"$T/x.txt" 2>&1; then
		ko "il display $SCHERMO non risponde"
		sed -n '1,3p' "$T/x.txt" | sed 's/^/        /'
		exit 2
	fi
	inf "risoluzione: $(sed -n 's/^  dimensions: *\([0-9]*x[0-9]*\) pixels.*/\1/p' "$T/x.txt" | head -1)"

	log "4. ⛔ IL GUASTO INNESTATO SU D16 — «senza flusso non si serve»"
	# ⭐ Il giro sano→guasto→risanato applicato alla cura di stasera: se
	#    `serve` non si rifiutasse, la cura sarebbe una frase.  ⛔ Su una
	#    porta e un CERTDIR finti: la 7516 dell'utente non si sfiora.
	mkdir -p "$T/vuoto" "$T/certfinto"
	SEQUENZE=$T/vuoto CERTDIR=$T/certfinto PORTA=7537 GIRO=guasto-d16 \
		bash "$0" serve > "$T/guasto.log" 2>&1
	ST_G=$?
	if [ "$ST_G" -eq 0 ]; then
		ko "⛔ senza sequenze serve ha servito lo stesso (stato 0)."
		ko "   E' D16 vivo: la cura non c'e'."
		ESITO=1
	else
		ok "senza sequenze serve si e' rifiutato (stato $ST_G)"
		sed -n '/IL FLUSSO/,$p' "$T/guasto.log" | sed 's/^/        /' | head -8
	fi
	if ss -ltn "sport = :7537" | grep -q ":7537"; then
		ko "⛔ e per giunta ha lasciato acceso qualcosa sulla 7537"
		[ -s "$T/certfinto/raccoglitore.pid" ] && \
			kill "$(cat "$T/certfinto/raccoglitore.pid")" 2>/dev/null
		ESITO=1
	else
		ok "e non ha acceso niente sulla 7537: «rifiutarsi» vuol dire questo"
	fi

	log "5. Il raccoglitore di certificazione, sulla $PORTA_C"
	if ss -ltn "sport = :$PORTA_C" | grep -q ":$PORTA_C"; then
		ko "la porta $PORTA_C e' occupata:"
		ss -ltnp "sport = :$PORTA_C" | sed 's/^/        /'
		exit 3
	fi
	: > "$REG_C"
	REGISTRO_SONDA=$(basename "$REG_C") python3 -u "$QUI/02-giudizio-raccogli.py" \
		"$PORTA_C" - - "$QUI" > "$T/racc.log" 2>&1 &
	PID_C=$!
	sleep 1
	if [ ! -d "/proc/$PID_C" ]; then
		ko "il raccoglitore di certificazione non e' partito:"
		sed 's/^/        /' "$T/racc.log"
		exit 3
	fi
	ok "acceso in chiaro su http://127.0.0.1:$PORTA_C (registro a parte)"

	attendi_fine() {
		local giro=$1 secondi=$2 i=0
		while [ "$i" -lt "$secondi" ]; do
			if grep -q "\"FINITO\".*$giro\|$giro.*\"FINITO\"" "$REG_C" 2>/dev/null; then
				return 0
			fi
			sleep 1; i=$((i + 1))
		done
		return 1
	}

	prova_motore() {
		local nome=$1 binario=$2 giro=$3; shift 3
		log "6. $nome — giro $giro"
		if ! command -v "$binario" >/dev/null; then
			inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
			return 0
		fi
		inf "versione: $("$binario" --version 2>&1 | head -1)"
		python3 "$QUI/02-giudizio-flusso.py" "$giro" >/dev/null || {
			ko "il flusso di $giro non si costruisce"; ESITO=1; return 0; }
		GIRI+=("$giro")
		local url="http://127.0.0.1:$PORTA_C/02-giudizio-pagina.html?giro=$giro&auto=2,4"
		env -u WAYLAND_DISPLAY DISPLAY=$SCHERMO "$@" "$url" >"$T/$nome.log" 2>&1 &
		local pid=$!
		if attendi_fine "$giro" "${ATTESA:-120}"; then
			ok "$nome ha finito il giro"
		else
			ko "$nome non ha scritto FINITO entro ${ATTESA:-120} s"
			tail -6 "$T/$nome.log" | sed 's/^/        /'
			ESITO=1
		fi
		kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
		sleep 1
	}

	MARCA=$(date +%s)
	prova_motore chrome google-chrome "certifica-chrome-$MARCA" \
		google-chrome --ozone-platform=x11 \
		--user-data-dir="$T/profilo-chrome" --no-first-run \
		--no-default-browser-check --disable-sync --window-size=900,800
	mkdir -p "$T/profilo-firefox"
	prova_motore firefox firefox "certifica-firefox-$MARCA" \
		firefox --no-remote --profile "$T/profilo-firefox"
	# ⛔⭐ IL GUASTO INNESTATO, ed e' il buco che curare D17 apre: il Chrome
	#     del portatile con uno **user agent da telefono**.  Il vecchio
	#     riconoscimento lo prendeva per un telefono; il nuovo deve
	#     rifiutarlo lo stesso, **per l'indirizzo**.
	prova_motore chrome-travestito google-chrome "certifica-travestito-$MARCA" \
		google-chrome --ozone-platform=x11 \
		--user-data-dir="$T/profilo-travestito" --no-first-run \
		--no-default-browser-check --disable-sync --window-size=900,800 \
		--user-agent="Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36"

	log "7. ⭐ LA CATENA, PRIMA DEL VERDETTO — che cosa ha funzionato"
	python3 - "$REG_C" "${GIRI[@]}" <<'PY'
import json, sys
righe = []
for r in open(sys.argv[1], encoding="utf-8"):
    r = r.strip()
    if r:
        try:
            righe.append(json.loads(r))
        except Exception:
            pass
esito = 0
for giro in sys.argv[2:]:
    mie = [r for r in righe
           if giro in json.dumps(r.get("dati", {}), ensure_ascii=False)
           or giro in (r.get("percorso") or "") or giro in (r.get("nome") or "")]
    pagina = [r for r in mie if r.get("tipo") == "richiesta"
              and "pagina.html" in (r.get("percorso") or "")]
    flusso = [r for r in mie if r.get("tipo") == "richiesta"
              and "flusso-" in (r.get("percorso") or "")]
    pixel = [r for r in mie if r.get("tipo") == "pixel"]
    ident = [r for r in mie if (r.get("dati") or {}).get("tipo") == "identita"]
    print("\n    == %s" % giro)
    def riga(marca, testo):
        print("    %s  %s" % ("\033[1;32mOK\033[0m" if marca
                              else "\033[1;31mNO\033[0m", testo))
    riga(pagina and pagina[0].get("codice") == 200,
         "la pagina e' stata servita: %s" % [r.get("codice") for r in pagina])
    riga(flusso and all(r.get("codice") == 200 for r in flusso),
         "il flusso e' stato servito: %s" % [r.get("codice") for r in flusso])
    if ident:
        d = ident[0]["dati"]
        riga(d.get("sequenze_dipinte", 0) > 0,
             "sequenze dipinte: %d su %d" % (d.get("sequenze_dipinte", 0),
                                             d.get("sequenze_date", 0)))
        for c in d.get("conti", []):
            print("        %s %-20s %-16s supportata=%s fotogrammi=%s%s"
                  % ("✔" if c.get("dipinto") else "✗", c.get("nome"),
                     c.get("codec"), c.get("supportata"), c.get("fotogrammi"),
                     ("  ⛔ " + (c.get("errore_configure") or
                                (c.get("errori") or ["—"])[0])[:70])
                     if not c.get("dipinto") else ""))
    else:
        riga(False, "nessun esito «identita»: il bottone 2 non e' arrivato in fondo")
        esito = 1
    riga(pixel, "pixel arrivati: %d file, %d byte in tutto"
         % (len(pixel), sum(r.get("byte", 0) for r in pixel)))
    if not (pagina and flusso and pixel):
        esito = 1
sys.exit(esito)
PY
	[ $? -ne 0 ] && { ko "la catena NON ha funzionato: un «rifiutato» su una"
		ko "   catena rotta non certifica niente"; ESITO=1; }

	log "8. ⛔ E ADESSO IL VERDETTO: dev'essere RIFIUTATO"
	python3 "$QUI/02-giudizio-dispositivo.py" "$REG_C"
	ST=$?
	if [ $ST -eq 3 ]; then
		ok "⛔ RIFIUTATO — come dev'essere: la catena ha funzionato in tutti i"
		ok "   suoi pezzi, i pixel sono arrivati, e il banco NON li accetta"
		ok "   perche' vengono da QUESTA macchina.  Forma E10, chiusa."
	else
		ko "⛔ il giro del PORTATILE e' stato ACCETTATO (stato $ST)."
		ko "   E' il buco che curare D17 poteva aprire, ed e' aperto."
		ESITO=1
	fi

	log "9. Il controllo positivo in coda"
	N=$(wc -l < "$REG_C")
	if [ "$N" -gt 0 ]; then
		ok "$N righe nel registro di certificazione ($REG_C)"
	else
		ko "ZERO righe: il portatore degli esiti non funziona"
		ESITO=1
	fi
	inf "⛔ e nessuna di queste righe e' una misura di S2: certificano lo"
	inf "   STRUMENTO.  Il registro dell'utente ($REGISTRO) non e' stato"
	inf "   toccato, e il raccoglitore sulla $PORTA e' rimasto acceso."

	# ⛔ I pixel di questo giro si BUTTANO, e il registro li ricorda (nome e
	#    byte).  Sono pixel del PORTATILE: lasciarli in cartella accanto a
	#    quelli del telefono e' il modo in cui la forma E10 rientra dalla
	#    porta di servizio il giorno che qualcuno guarda i file invece del
	#    registro.
	N_P=$(ls "$QUI"/pagina-certifica-*.rgb24 2>/dev/null | wc -l)
	rm -f "$QUI"/pagina-certifica-*.rgb24 "$QUI"/flusso-certifica-*.json \
	      "$QUI"/flusso-guasto-d16.json
	inf "buttati $N_P file di pixel del portatile (il registro li ricorda)"

	log "Esito"
	if [ "$ESITO" -eq 0 ]; then
		ok "il banco fa quel che ha dichiarato"
	else
		ko "qualcosa non torna — vedi sopra"
	fi
	exit "$ESITO"
	;;

procedura)
	cat <<'TESTO'

⛔ CHE COSA SERVE DALL'UTENTE — la sonda sul telefono vero non si fa da soli

  Dispositivo   un TELEFONO Android con Chrome aggiornato (≥ 108; si legge in
                chrome://version e SI SCRIVE accanto al numero).
                ⛔ NON il Chrome del portatile: e' la forma d'errore E10.
                ⭐ Se c'e' anche un iPhone con Safari ≥ 16.4, si fa due volte:
                   sono due sili diversi, e la copertura di campo non e' la
                   stessa.  Su iPhone pero' il controllo C non esiste (vedi
                   sotto), e il limite va scritto.

  Rete          il telefono sulla STESSA rete del portatile (WiFi di casa).
                Niente rete mobile: qui si misura la decodifica, non la linea.

  Cavo          ⭐ e per il controllo C, un CAVO USB fra telefono e portatile,
                con il debug USB acceso.  E' l'unico canale che risponde
                davvero: `chrome://inspect` → la scheda del telefono →
                «inspect» → `chrome://media-internals`, e si cerca la riga
                  Created MediaCodec <nome>, is_software_codec=<bool>
                ⛔ Se il nome comincia per `c2.android.` o `omx.google.` e'
                   SOFTWARE, punto — anche se `prefer-hardware` era riuscito.
                ⚠ Su iPhone questo canale NON esiste: li' il verdetto poggia
                  solo sui numeri, e va scritto come limite dichiarato.

  Gesto         1. sul portatile:  bash banchi/02-giudizio-telefono.sh serve
                2. sul telefono:   si apre l'indirizzo stampato **per intero**,
                                   con il `?giro=…` in fondo;
                                   ⚠ comparira' l'avviso del certificato: si
                                   accetta UNA volta («Avanzate» → «Procedi»).
                3. si preme il bottone 1 e si aspetta che finisca;
                4. si preme il bottone 2;
                5. ⛔ SCHERMO ACCESO e scheda in PRIMO PIANO per tutta la
                   misura: una scheda in secondo piano si congela dopo cinque
                   minuti, e il banco misurerebbe il congelamento invece del
                   calore.

  ⛔ L'INDIRIZZO NON SI ACCORCIA E NON SI RIUSA.  Il `?giro=…` non e' un
     ornamento: il flusso da decodificare si chiama `flusso-<giro>.json`, e un
     indirizzo con un giro vecchio (o senza giro) fa arrivare la pagina a un
     404.  ⚠ E' esattamente quel che e' successo il 12 agosto: gli «esiti
     negativi» erano il banco che non aveva dato niente da decodificare.
     ⇒ Per un secondo tentativo si chiede un indirizzo nuovo con
       `bash banchi/02-giudizio-telefono.sh flusso`, che NON spegne niente e
       NON fa ricomparire l'avviso del certificato.

═══ ⭐ E SE IL TELEFONO E' IN SAMSUNG DeX — che e' un caso a se' ═══════════

  Che cos'e'    il telefono attaccato a un monitor (o a una finestra sul
                portatile): schermo grande, mouse, finestre.  ⛔ Il silicio e
                MediaCodec sono **quelli del telefono**, quindi per la domanda
                di S2 — «il decodificatore del telefono decodifica HEVC Main10
                in hardware?» — DeX **vale**.
                ⚠ Vale MENO per il calore e il consumo: in DeX il telefono sta
                  su un dock e spesso in carica, e il decadimento su dieci
                  minuti misurerebbe un altro regime termico.  Si dichiara.

  Che cosa      ⛔ Chrome in DeX manda uno user agent da DESKTOP —
  inganna          `Mozilla/5.0 (X11; Linux x86_64) … Chrome/150…`
                — indistinguibile da un portatile.  ⇒ Il banco NON riconosce
                piu' il dispositivo dalla stringa: usa l'indirizzo di
                provenienza (chi non e' il portatile ne' il server e' un terzo
                dispositivo) piu' l'impronta che la pagina raccoglie
                (`userAgentData`, GPU WebGL, tocco, puntatore, schermo).
                ⭐ Il registro **dice DeX**: non deve scegliere fra «telefono»
                   e «desktop», perche' DeX non e' ne' l'uno ne' l'altro.

  Il cavo,      ⛔ IL CAVO USB E' L'UNICO CANALE CHE DICE «HARDWARE» CON
  in DeX           CERTEZZA (`chrome://inspect` → «inspect» →
                   `chrome://media-internals` → `Created MediaCodec <nome>,
                   is_software_codec=<bool>`).  ⚠ E IN DeX LA PORTA PUO'
                   ESSERE OCCUPATA: se DeX gira **via cavo** verso un monitor
                   o verso il portatile, quella e' l'unica porta USB-C del
                   telefono e il debug non ci passa.  Tre strade, in ordine:
                     1. **DeX senza fili** (Smart View verso una TV / un
                        monitor) e il cavo USB libero per `chrome://inspect`;
                     2. un **hub USB-C** con presa dati separata;
                     3. ⚠ si rinuncia al controllo C **e lo si dichiara**: il
                        verdetto sull'hardware resta `[?]`, e i numeri della
                        portata da soli **non** lo chiudono.
                ⛔ Quel che NON si fa: dire «hardware» perche' i numeri sono
                   alti.  Un `c2.android.hevc.decoder` in puro software supera
                   cinque prove su otto.

  Tempo         ~10 minuti per i bottoni 1, 2 e 4 — ⭐ e il secondo tentativo
                costa **due minuti**: l'indirizzo nuovo si apre e basta,
                l'eccezione del certificato e' gia' accettata.
                ⏳ + 10 minuti di fila per il decadimento (bottone 3), che e'
                la firma piu' difficile da falsificare — e si fa quando le
                sequenze di F2.3 ci sono.

  ⛔ E QUEL CHE NON SI PUO' CHIEDERE ALL'UTENTE: di dire se «si vede bene».
     Questa sonda produce numeri.  Il giudizio di I8 — «il metro e' quel che
     l'utente vede» — arriva alla fine della fase, sul desktop suo, non qui.

TESTO
	;;

spegni)
	if [ -s "$PIDFILE" ] && [ -d "/proc/$(cat "$PIDFILE")" ]; then
		kill "$(cat "$PIDFILE")" && ok "raccoglitore spento"
	else
		inf "non era acceso"
	fi
	rm -f "$PIDFILE"
	;;

*)
	printf 'uso: %s {serve|flusso|procedura|controllo|analizza|certifica|spegni}\n' "$0"
	exit 2 ;;
esac
