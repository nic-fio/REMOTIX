#!/bin/bash
#
# 02-giudizio-telefono.sh — F2.6 (b): LA SONDA SUL DISPOSITIVO VERO.
#                           `PIANO.md` §1.2 domanda S2, e fase 2.
#
#   bash banchi/02-giudizio-telefono.sh serve      accende il sito e stampa l'indirizzo
#   bash banchi/02-giudizio-telefono.sh procedura  ⛔ che cosa serve dall'utente
#   bash banchi/02-giudizio-telefono.sh controllo  ⛔ il canale di lettura funziona?
#   bash banchi/02-giudizio-telefono.sh analizza   legge il registro e giudica i pixel
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
# ⛔ E IL SECONDO CONTROLLO: LA PAGINA E' ARRIVATA A UN BROWSER?
#
# Il registro porta lo `User-Agent` di ogni riga.  ⛔ Se il gettone di prova
# c'e' ma **nessuna riga porta un user agent di telefono**, il verdetto e'
# «il dispositivo non e' arrivato», non «il dispositivo ha fallito».
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

	log "2. Il raccoglitore sulla $PORTA"
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

	log "3. L'indirizzo da aprire SUL TELEFONO"
	printf '\n        https://%s:%s/02-giudizio-pagina.html?giro=%s\n\n' \
		"$(indirizzo)" "$PORTA" "$GIRO"
	inf "⚠ comparira' l'avviso del certificato: si accetta UNA volta."
	inf "  E' esattamente il meccanismo che S1b sta misurando sulla 7452."
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

	log "1. Chi e' arrivato alla pagina"
	if [ ! -s "$REGISTRO" ]; then
		ko "il registro e' vuoto.  ⛔ Ma il canale funziona (l'ho appena"
		ko "   provato): quindi «vuoto» qui vuol dire davvero «nessuno e'"
		ko "   arrivato», e non «non ho potuto guardare»."
		exit 2
	fi
	python3 - "$REGISTRO" <<'PY'
import json, sys, re
righe = [json.loads(r) for r in open(sys.argv[1]) if r.strip()]
ua = {}
for r in righe:
    u = r.get("ua", "")
    if u:
        ua[u] = ua.get(u, 0) + 1
telefono = [u for u in ua if re.search(r"Android|iPhone|iPad|Mobile", u)]
print("    --  %d righe nel registro, %d user agent distinti" % (len(righe), len(ua)))
for u, n in ua.items():
    marca = "📱" if u in telefono else "💻"
    print("    --  %s %3d × %s" % (marca, n, u[:100]))
if not telefono:
    print("    \033[1;31mNO\033[0m  ⛔ NESSUNA riga viene da un dispositivo mobile.")
    print("        Il verdetto e' «il dispositivo non e' arrivato», NON «il")
    print("        dispositivo ha fallito».  Un giro sul browser del portatile")
    print("        certifica lo STRUMENTO e non misura S2: e' la forma E10.")
    sys.exit(3)
PY
	st=$?
	[ $st -eq 3 ] && exit 2

	log "2. I pixel — ⛔ e qui si chiude la meta' (a) sul dispositivo VERO"
	PAG=$(ls -t "$QUI"/pagina-*.rgb24 2>&1 | head -1)
	if [ ! -s "$PAG" ]; then
		ko "nessun file di pixel e' arrivato dalla pagina."
		ko "   ⛔ Con il canale sano e un dispositivo arrivato, questo vuol dire"
		ko "      che la rilettura della tela e' fallita sul dispositivo — che e'"
		ko "      un fatto da scrivere, non un silenzio."
		exit 2
	fi
	inf "pixel arrivati: $PAG"
	inf "⇒ il giudizio si da' con:"
	inf "   bash banchi/02-giudizio-confronto.sh giudica --scena … \\"
	inf "        --cattura … --riferimento … --pagina $PAG \\"
	inf "        --colore … --riferimento-10 … --identita-pagina …"
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
                2. sul telefono:   si apre l'indirizzo stampato;
                                   ⚠ comparira' l'avviso del certificato: si
                                   accetta UNA volta («Avanzate» → «Procedi»).
                3. si preme il bottone 1 e si aspetta che finisca;
                4. si preme il bottone 2;
                5. ⛔ SCHERMO ACCESO e scheda in PRIMO PIANO per tutta la
                   misura: una scheda in secondo piano si congela dopo cinque
                   minuti, e il banco misurerebbe il congelamento invece del
                   calore.

  Tempo         ~10 minuti per i bottoni 1, 2 e 4.
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
	printf 'uso: %s {serve|procedura|controllo|analizza|spegni}\n' "$0"
	exit 2 ;;
esac
