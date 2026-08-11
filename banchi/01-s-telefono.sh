#!/bin/bash
#
# 01-s-telefono.sh — il banco delle tre misure che vogliono un DISPOSITIVO che
# stanotte non c'e': S2 (telefono + PC), S3a (DeX), S6 (telefono su LTE).
#
#   bash banchi/01-s-telefono.sh serve        accende il sito e stampa gli indirizzi
#   bash banchi/01-s-telefono.sh s2           la procedura di S2, passo per passo
#   bash banchi/01-s-telefono.sh s3a          la procedura di S3a
#   bash banchi/01-s-telefono.sh s6           la procedura di S6
#   bash banchi/01-s-telefono.sh analizza     legge il registro e classifica i tre stati
#   bash banchi/01-s-telefono.sh spegni       spegne il sito
#
# ---------------------------------------------------------------------------
# ⛔ QUESTO FILE NON PRODUCE NESSUN NUMERO, E NON DEVE.
#
# S2, S3a e S6 pretendono ferro che alla data di scrittura (10 agosto 2026,
# notte) non e' collegato: il telefono Android, il DeX, una rete LTE vera.
# ⛔ Dedurre un esito da questa macchina sarebbe la forma d'errore **E5**, e in
# questo progetto un `[M]` falso costa piu' di una misura mancante.
#
# Quel che c'e' qui e' **il banco pronto a girare**: le pagine, i controlli che
# i rapporti prescrivono, e la procedura — perche' il giorno che il
# dispositivo c'e', la misura costi un pomeriggio invece di una settimana.
#
# ---------------------------------------------------------------------------
# ⭐ PERCHE' IL SITO E' QUELLO DI S1b
#
# Tutt'e tre le pagine vogliono un **contesto sicuro**: WebCodecs, la keyboard
# lock, gli appunti e WebTransport non esistono in HTTP semplice.  Il sito in
# HTTPS di S1b (`01-s1b-sito.sh`) serve gia' l'intera cartella con un
# certificato longevo e stabile: si riusa quello.  ⚠ Sul telefono comparira'
# l'avviso del certificato **una volta**: si accetta, e da li' in poi il
# contesto e' sicuro (e' esattamente il meccanismo che S1b sta misurando).
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7452}
CERTDIR=${CERTDIR:-/media/REMOTIX/s1b-certificato}
SRC=/media/REMOTIX/src
ssh_() { python3 "$RADICE/v1/strumenti/sshpw.py" "$@"; }

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31m⛔\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

case "${1:-serve}" in
serve)
	log "Il sito in HTTPS, sul server"
	ssh_ "bash $SRC/01-s1b-sito.sh accendi $IND $PORTA $CERTDIR"
	G=$(date +%s)
	log "Gli indirizzi da aprire sul dispositivo"
	printf '    S2  : https://%s:%s/01-s2-pagina.html?giro=s2-%s\n' "$IND" "$PORTA" "$G"
	printf '    S3a : https://%s:%s/01-s3a-pagina.html?giro=s3a-%s\n' "$IND" "$PORTA" "$G"
	printf '    S6  : https://%s:%s/01-s6-pagina.html?giro=s6-%s&percorso=LTE&url=…&impronta=…\n' \
	    "$IND" "$PORTA" "$G"
	inf "il registro di tutte e tre si accumula in $SRC/01-s1b-visite.jsonl sul server"
	;;

spegni)
	ssh_ "bash $SRC/01-s1b-sito.sh spegni"
	;;

s2)
	log "S2 — HEVC Main10 in hardware.  ⛔ NON ESEGUITA: manca il telefono."
	cat <<'TESTO'
    Che cosa serve, e perche' senza non si parte:

      · il TELEFONO Android con Chrome — ⛔ e non «il Chrome del portatile»:
        e' la forma d'errore E10 (DECISIONI.md §5-bis.0-ter).  Su Android il
        decodificatore vive dietro MediaCodec, che e' precisamente la cosa che
        rende inutili i segnali JS: quel che si misura qui non esiste altrove.
      · un PC COLLEGATO per `chrome://inspect` — il controllo C, l'unico
        canale che risponde davvero.
      · ⛔ le CINQUE SEQUENZE da `hevc_vaapi` (S2 §4.1), che sono della fase 2.
        Senza, la pagina misura i due controlli e **dichiara assenti** le
        sequenze HEVC.  Non le sostituisce con una piu' facile: una sequenza
        piu' facile non misura «un po' meno», misura un'altra cosa.

    L'ordine, e il primo passo non e' HEVC:

      1. ⛔ I DUE CONTROLLI, e il banco non pubblica verdetti finche' non
         passano (S2 §4.4):
            A — VP9 `prefer-software`  DEVE risultare software
            B — VP9 `prefer-hardware`  DEVE risultare hardware
         ⭐ La sequenza D la costruisce la pagina da se' con `VideoEncoder`:
            questi due controlli **non aspettano la fase 2**.
      2. Le misure su HEVC: portata a saturazione, canarina di CPU nel worker,
         e ⛔ **dieci minuti** — perche' e' solo li' che il software non riesce
         piu' a fingere (energia ×13,76 da 720p a 2160p, S2 §3.8).
      3. Il decadimento, con lo schermo acceso e la scheda in primo piano: una
         scheda in secondo piano si congela dopo cinque minuti, e il banco
         misurerebbe il congelamento invece del calore.

    Le tre letture, e sono TRE non due:
         ≥ 90 fps  ⇒ hardware
         ≤ 30 fps  ⇒ software
         in mezzo  ⇒ ⛔ VERDETTO SOSPESO, si guardano gli altri numeri
    Canarina: > 0,85 hardware · < 0,4 software.  Decadimento: > 0,9 · < 0,6.

    ⛔ CONTROLLO C — la verita' fuori da JavaScript, e non e' automatizzabile:
      1. telefono in debug USB, collegato al PC;
      2. sul PC: `chrome://inspect` → la scheda del telefono → «inspect»;
      3. nella finestra remota apri `chrome://media-internals`;
      4. cerca la riga  `Created MediaCodec <nome>, is_software_codec=<bool>`;
      5. se il nome comincia per `c2.android.` o `omx.google.` ⇒ **software,
         punto**, anche se `prefer-hardware` era riuscito.
      ⛔ Se anche UN SOLO dispositivo mostra `is_software_codec=true` con
         `prefer-hardware` riuscito, e' la conferma sul campo del [R] di
         S2 §3.3 e va scritta in DECISIONI.md come fatto misurato.
      ⚠ Su iPhone questo canale non esiste: li' il verdetto poggia solo sui
         numeri, e va scritto come limite dichiarato.

    ⛔ E l'atteso di S2 e' `[?]`, non «si' da Chrome 108»: quel [S] riguarda il
       supporto in WebCodecs, non l'hardware.
TESTO
	;;

s3a)
	log "S3a — la tastiera nei tre stati.  ⛔ NON ESEGUITA: manca il DeX."
	cat <<'TESTO'
    ⛔ DUE VERIFICHE PRIMA DI COMINCIARE, o si misura un'altra cosa:

      1. ⛔ IL DeX DEV'ESSERE ALMENO ANDROID 16 QPR1.  La lock esiste solo da
         li': su un DeX piu' vecchio il banco misurerebbe **l'assenza della
         lock** e la scambierebbe per scorciatoie perdute.
         Si legge in Impostazioni → Informazioni → Versione software, e si
         SCRIVE accanto al numero.
      2. ⛔ FIREFOX DESKTOP: serve la 151, e su questa macchina c'e' la 140.0
         [M].  `requestFullscreen({keyboardLock})` e' entrato in Gecko nella
         151: chi provasse qui misurerebbe l'assenza della lock.  ⇒ la riga
         «Firefox/Linux» di S3 §4.4 **non e' eseguibile su questa macchina**, e
         non si sostituisce con Chrome.

    L'ordine (S3 §4.3), e non e' un dettaglio:
      · si comincia dai QUATTRO CONTROLLI POSITIVI (§4.2), a OGNI motore;
      · le combinazioni vanno dalla meno rischiosa alla piu' rischiosa, UNA
        PER VOLTA;
      · ⛔ `Ctrl+T`, `Ctrl+N`, `Ctrl+W` per ULTIME: chiudono la scheda e
        porterebbero via il registro.
      ⭐ Qui il registro e' gia' fuori: ogni evento parte per il server nel
        momento in cui succede (`sendBeacon`), e la pagina manda una riga
        «ARMATO» prima di ogni combinazione.  E' cosi' che il registro del
        server distingue i tre stati da solo — vedi `analizza`.

    ⛔ E lo schermo intero si entra DA JAVASCRIPT, mai con F11: con F11 la lock
       non esiste e nessuno lo dice, e tutte le prove che seguono non valgono
       niente.

    ⛔ La lock si prova per EFFETTO, non per esistenza: `requestFullscreen`
       ignora in silenzio le opzioni che non conosce, quindi «la promessa si e'
       risolta» non e' «blocca».  Dopo averla chiesta si prova una riservata
       (Ctrl+T) e si guarda che cosa succede davvero.

    I sei accoppiamenti motore-sistema di S3 §4.4 (non «due motori»):
       1 Chrome/Linux-Wayland · 2 Firefox≥151/Linux-Wayland · 3 Chrome/Windows
       4 ⭐ Chrome su Samsung DeX (l'uso primario) · 5 Safari/macOS
       6 Safari/iPadOS con tastiera fisica
    ⚠ La riga 4 NON si deduce dalla 1.
TESTO
	;;

s6)
	log "S6 — il carico utile di un datagram.  ⛔ NON ESEGUITA: manca la LTE."
	cat <<'TESTO'
    ⛔ NON E' UNA GRANDEZZA DEL MOTORE: lo decide il cammino.  Quindi il
       percorso si dichiara accanto al numero, e la pagina si RIFIUTA di
       misurare senza `?percorso=` — un numero senza percorso sono due misure
       diverse sotto la stessa etichetta (E2, rilievo R3.22).

    Che cosa serve:
      · il TELEFONO su LTE vera (o una VPN a MTU 1400): ⛔ il percorso
        PEGGIORE che si intende servire, non quello comodo.  Misurare in LAN e
        alzare il tetto significa spedire audio che l'utente non riceve.
      · un server WebTransport che ⛔ **fa l'eco dei datagram**.  Senza eco la
        pagina non misura niente e lo dice: il suo primo passo e' un
        controllo positivo da 64 byte, e se quello non torna la prova si ferma.
      · l'impronta del certificato di sessione, da passare in `?impronta=`.

    Il numero che decide: **972 byte** — 480 campioni × 2 canali × 2 byte + 12
    di intestazione, cioe' il PCM a 5 ms di RCP §5.3.  Sotto quella soglia il
    blocco audio va accorciato.  ⚠ E se il numero deve diventare un tetto di
    protocollo, S6 dice di non misurarlo affatto e di prendere il minimo
    garantito da QUIC.

    Il controllo: si spedisce un datagram di quella misura esatta e ⛔ **si
    verifica che arrivi dall'altra parte**, non che l'API lo accetti.  Un
    datagram troppo grande si perde in silenzio — ed e' precisamente il modo in
    cui il PCM non partirebbe mai senza che niente lo dica.

    ⚠ `maxDatagramSize` dichiarato dall'API si registra e non si crede: e' la
      promessa del motore, non la portata del cammino.  Se i due numeri non
      coincidono, quello che conta e' quello misurato.
TESTO
	;;

analizza)
	log "I tre stati, letti dal registro del server"
	# ⛔ RILIEVO A28, 11 agosto 2026, e sono DUE difetti nella stessa riga.
	#
	#  (a) `ssh_ "cat …" >/tmp/… 2>/dev/null`: se `ssh` non parte, il file locale
	#      e' vuoto e **la ragione e' stata buttata**.  Il testo che seguiva era
	#      onesto — «nessuno ha misurato», non «nessuna scorciatoia arriva» — ma
	#      la riga dopo era `sys.exit(0)`: ⛔ **lo stato d'uscita diceva
	#      riuscito**.  E' il `2>/dev/null` che nasconde una diagnosi di
	#      `LEZIONI.md` §1.9, con in piu' uno zero addosso.
	#
	#  (b) e anche nel cammino buono `analizza` non confrontava niente e non
	#      usciva mai ≠ 0: trovare uno stato **B — CONSEGNATA E RISERVATA**, che
	#      e' il caso pericoloso per cui S3a esiste, produceva una riga di testo
	#      e uscita 0.  ⛔ B0.4 vuole che lo stato d'uscita sia quello del
	#      CONFRONTO.
	#
	# ⛔ Da cui: lo stderr si tiene, lo stato d'uscita del comando remoto se lo
	#    stampa il comando stesso, e gli esiti sono QUATTRO — 0 nessuno stato B ·
	#    1 almeno uno stato B · 2 nessuna riga da guardare · 3 non ho potuto
	#    leggere il registro.
	REG=/tmp/s3a-registro.jsonl
	rm -f "$REG"
	TUTTO=$(ssh_ "cat $SRC/01-s1b-visite.jsonl 2>&1; printf 'S3A-FINE=%s\n' \$?" 2>&1)
	STATO=$(printf '%s\n' "$TUTTO" | sed -n 's/^S3A-FINE=\([0-9][0-9]*\)$/\1/p')
	printf '%s\n' "$TUTTO" | grep -v '^S3A-FINE=' > "$REG"
	if [ -z "$STATO" ]; then
		ko "il comando remoto non e' arrivato in fondo: nessun «S3A-FINE»."
		ko "⛔ Questo NON e' «nessuna riga nel registro»: e' «non ho potuto"
		ko "   guardare», e i due hanno cure diverse.  Quel che e' tornato:"
		sed -n '1,5p' "$REG" | sed 's/^/        /'
		exit 3
	fi
	if [ "$STATO" -ne 0 ]; then
		ko "il registro del server non si e' letto (cat esce $STATO):"
		sed -n '1,5p' "$REG" | sed 's/^/        /'
		ko "⛔ «non ho potuto leggere» non e' «nessuno ha misurato»."
		exit 3
	fi
	ok "registro letto dal server: $(wc -l < "$REG") righe"
	python3 - "$REG" <<'PY'
import json, sys

# ⛔ LA CLASSIFICAZIONE NEI TRE STATI, E LA FA IL BANCO (B0.4).
#
#   ARMATO + keydown + la pagina vive     ⇒ A  consegnata e annullata
#   ARMATO + keydown + PAGEHIDE           ⇒ B  ⛔ consegnata E il browser agisce
#   ARMATO + niente  + PAGEHIDE           ⇒ C  non consegnata, e il browser agisce
#   ARMATO + niente  + la pagina vive     ⇒ C  non consegnata, e non e' successo niente
#
# ⛔ Senza la distinzione fra B e C il banco «conta» invece di ascoltare, e
#    dichiara innocuo il caso pericoloso (rilievo R3.11).
righe = []
for r in open(sys.argv[1], encoding="utf-8"):
    try:
        righe.append(json.loads(r))
    except Exception:
        pass
tutte = len(righe)
righe = [d for d in righe if str(d.get("giro", "")).startswith("s3a")]
print(f"    denominatore: {tutte} righe nel registro, {len(righe)} di S3a")
if not righe:
    print("    nessuna riga di S3a nel registro: la misura non e' stata eseguita.")
    print("    ⛔ E questo NON e' «nessuna scorciatoia arriva»: e' «nessuno ha misurato».")
    # ⛔ E lo stato d'uscita lo dice: uscire 0 qui vorrebbe dire consegnare a
    #    chiunque legga solo `$?` un «tutto a posto» su zero misure — la forma
    #    di verde piu' insidiosa di `LEZIONI.md` §1.9 regola 6.
    sys.exit(2)

blocchi, corrente = [], None
for d in righe:
    if d.get("tipo") == "ARMATO":
        corrente = {"cosa": d.get("cosa"), "keydown": [], "pagehide": False,
                    "annullato": None, "motore": d.get("motore", "")[:60],
                    "lock": d.get("lock"), "schermo": d.get("schermoIntero")}
        blocchi.append(corrente)
    elif corrente is not None:
        if d.get("tipo") == "KEYDOWN":
            corrente["keydown"].append(d.get("code"))
        elif d.get("tipo") == "KEYDOWN_DOPO":
            corrente["annullato"] = d.get("annullato")
        elif d.get("tipo") == "PAGEHIDE":
            corrente["pagehide"] = True

print(f"    {len(blocchi)} combinazioni armate\n")
print(f"    {'combinazione':38s} {'arrivata':9s} {'browser ha agito':17s} stato")
pericolose = []
for b in blocchi:
    arrivata = bool(b["keydown"])
    agito = b["pagehide"]
    if arrivata and not agito:
        stato = "A — consegnata e annullata"
    elif arrivata and agito:
        stato = "⛔ B — CONSEGNATA E RISERVATA (il peggiore)"
        pericolose.append(b["cosa"])
    elif not arrivata and agito:
        stato = "C — non consegnata, e il browser ha agito"
    else:
        stato = "C — non consegnata"
    print(f"    {str(b['cosa'])[:38]:38s} {'si' if arrivata else 'no':9s} "
          f"{'si' if agito else 'no':17s} {stato}")

# ⛔ E ADESSO IL CONFRONTO, che e' quel che mancava (B0.4): lo stato d'uscita
#    e' quello del confronto, non della lettura.  Lo stato B — la combinazione
#    arriva alla pagina **e** il browser agisce lo stesso — e' il caso
#    pericoloso per cui S3a esiste: consegnarlo come una riga di testo e uscire
#    0 vorrebbe dire lasciarlo passare a chiunque legga solo lo stato d'uscita.
if not blocchi:
    print("\n    ⛔ ZERO combinazioni armate: nessun esito.  Le righe di S3a")
    print("       ci sono ma nessuna dichiara un `ARMATO`, e senza quello non")
    print("       si distingue B da C — che e' la distinzione per cui S3a esiste.")
    sys.exit(2)
print(f"\n    == il denominatore: {len(blocchi)} combinazioni giudicate, "
      f"{len(blocchi) - len(pericolose)} approvate")
if pericolose:
    print(f"    ⛔ {len(pericolose)} combinazioni sono nello stato B — "
          f"CONSEGNATA E RISERVATA:")
    for c in pericolose:
        print(f"       {c}")
    print("       ⛔ La combinazione arriva alla pagina E il browser agisce lo")
    print("          stesso: la lock non protegge, e la scheda se ne va.")
    sys.exit(1)
print("    ⭐ nessuna combinazione nello stato B — e vale per queste, non per")
print("       quelle che non sono state provate.")
sys.exit(0)
PY
	;;
*) echo "uso: $0 {serve|s2|s3a|s6|analizza|spegni}" >&2; exit 2 ;;
esac
