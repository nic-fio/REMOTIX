#!/usr/bin/env bash
#
# ===========================================================================
# 07-b43 — L'AUDIO VERO: quello che suona DENTRO la sessione grafica.
# ===========================================================================
#
# `07-b41` + `07-b42` certificano il **filo**: il server fabbrica un tono
# (`--audio-prova 440`), il cliente lo raccoglie, il giudice lo ascolta.  ⭐ E'
# provato e non si rifa'.  ⛔ **Ma il tono lo fabbrica il server**: fra quel
# banco e l'utente manca tutta la meta' che conta — il **sink** nella sessione
# e la **cattura del suo monitor**.
#
# Questo banco allestisce la scena dell'audio vero:
#
#     un'applicazione DENTRO la sessione di `prova2` suona un tono noto
#          ↓  (sink «remotix», creato dal figlio nella sessione)
#     il monitor del sink, catturato dal prodotto
#          ↓  (datagram §6.3, PCM s16le 48 kHz)
#     `01-b3-cliente.py --audio-scrivi`   ← il secondo lettore di RCP
#          ↓
#     `07-b43-giudizio.py`  → che chiama `07-b42-giudice.py`, il giudice
#                             certificato su sei casi (`07-b40`)
#
# ---------------------------------------------------------------------------
# ⛔⛔ LE TRE REGOLE CHE `PIANO.md` IMPONE A QUESTO BANCO
# ---------------------------------------------------------------------------
#
# a) **SI ASCOLTA, NON SI CONTANO I BLOCCHI.**  In v1 il banco contava i
#    campioni mentre l'audio era **rumore a fondo scala**, e restava verde
#    (`LEZIONI.md` §2.2).  ⇒ Qui il verdetto lo da' `giudica()`: frequenza
#    dominante, RMS e ⭐ **purezza** — l'unico numero che distingue un tono da
#    rumore.  Il conto dei blocchi c'e', ma come **denominatore** (`LEZIONI.md`
#    §1.9 regola 4), mai come verdetto.
#
# b) **I DUE LATI SI SINCRONIZZANO CON MARCATORI, NON CON `sleep`.**  Al banco
#    degli appunti di KDE i due lati erano sfasati di **tredici secondi**, e il
#    controllo dava rosso su codice che funzionava (`LEZIONI.md`
#    §2.3-quinquies).  ⇒ Qui i marcatori sono **tre**, e nessuno e' un tempo:
#
#      M1  il cliente ha aperto la sessione   → il file di `--segnale`, che il
#          cliente scrive **dopo** `SESSIONE` (⭐ un file scritto e chiuso e'
#          un fatto; una riga stampata e' una speranza)
#      M2  il sink esiste nel grafo           → `pw-dump` dentro la sessione di
#          `prova2` trova un nodo `Audio/Sink` che si chiama «remotix»
#      M3  ⭐ **il tono sta DAVVERO suonando dentro quel sink** → nel grafo
#          esiste un **legame** (`Link`) il cui `link.input.node` e' il sink.
#          `[M]` 17 ago 2026, **due volte**: sul portatile (0 legami prima di
#          suonare, **2 legami `active`** mentre suona, 0 dopo) e ⭐ **dentro la
#          sessione viva di `prova2` sulla macchina di prova**, con `pw-play`
#          lanciato da `setpriv` come fa questo copione — 0 prima, **2**
#          durante.  ⛔ Non e' «ho lanciato
#          `pw-play`»: e' «il grafo dice che i campioni entrano nel sink»,
#          che e' la differenza fra un'intenzione e una misura (`LEZIONI.md`
#          §2.0, il riquadro: *«dichiarare un palco non e' averlo»*).
#
#    ⇒ E la finestra da giudicare **si calcola**, non si spera: e' quel che
#      resta fra M3 e la fine della presa, meno un margine.  Se non basta, il
#      banco lo **dice** invece di giudicare aria.
#
# c) **IL CONTROLLO POSITIVO**, cioe' *«come so che questo banco sa vedere il
#    difetto che cerca?»*  Sono cinque giri, e **due sono difetti innestati
#    apposta**: il banco e' verde solo se quei due gli fanno dire ROSSO.  La
#    tabella sta al §«I GIRI» qui sotto.
#
# ---------------------------------------------------------------------------
# ⛔ E IL CASO CHE VALE DA SOLO: IL VOLUME CHE NON ARRIVA AL MONITOR
# ---------------------------------------------------------------------------
#
# `STUDI.md` §kde §10.5, `[M]` 8 agosto 2026 e **l'ha aperta l'utente**: *«se
# abbasso il volume l'audio resta sempre alto»*.  In PipeWire il volume di un
# nodo si applica **a valle** della presa del monitor, e la proprieta' che
# sposta la presa — `monitor.channel-volumes` — vale **`false`** se non la si
# chiede.  ⇒ Chi cattura riceve il segnale **a fondo scala qualunque cosa dica
# il cursore, muto compreso**.
#
# ⭐⭐ **Il difetto e' stato RIPRODOTTO oggi, per certificare questo banco** —
# `[M]` 17 agosto 2026, portatile, PipeWire 1.4.2 (la stessa della macchina di
# prova), due sink gemelli creati con `pw-cli` e catturati sul monitor con
# `pw-cat`, tono 440 Hz ampiezza 0,5:
#
#   | volume del sink        | `monitor.channel-volumes=true` | `=false`        |
#   |------------------------|--------------------------------|-----------------|
#   | 100 % (cv 1,0)         | rms **0,3535**                 | rms 0,3535      |
#   | 25 %  (cv **0,015625**)| rms **0,0055**                 | ⛔ rms **0,3535** |
#   | muto                   | rms **0,0000**                 | ⛔ rms **0,3535** |
#
# ⭐ E i numeri della colonna buona non sono «quasi giusti»: 0,3535 × 0,015625
#    = **0,005523**, misurato **0,0055**.  Il 0,015625 e' 0,25³ — la curva
#    cubica di PulseAudio, che `wpctl set-volume 0.25` scrive nel nodo.
#    ⛔ Da cui la regola di questo banco: **l'atteso del giro col volume basso
#    si legge dal GRAFO** (`Props.channelVolumes`), non si scrive a mano.  Chi
#    si aspettasse «un quarto del segnale» darebbe rosso a un prodotto sano.
#
# ---------------------------------------------------------------------------
# ⛔ L'ISOLAMENTO — non e' pignoleria, e' il ban di `RCP.md` §4.4-bis
# ---------------------------------------------------------------------------
#
#   porta **7720** · albero `/media/REMOTIX/src/07-vero-src` ·
#   lavoro `/media/REMOTIX/tmp/07-vero` · unita' `remotix-7720.service` ·
#   ban-file, socket del comando, certificati e rilievo **propri**
#
# Il ban e' per **indirizzo** e dura **12 ore**: un banco che lo fa scattare
# mette fuori uso **tutti gli altri**, perche' partono tutti dallo stesso
# indirizzo.  ⛔⛔ **Le porte 7448, 7700 e 7710 non si toccano**: ci sono
# sopra dei banchi che stanno lavorando, e questo copione non le ferma **mai**
# — nemmeno per sbaglio, perche' spegne **la sua unita' per nome**.
#
# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE — due trappole gia' pagate
# ---------------------------------------------------------------------------
#
#  · la parola di `prova2` che PAM verifica sta nella riga **`chpasswd`** di
#    `src/provisiona.sh`.  ⛔ **NON** in `/media/REMOTIX/credenziali-banchi`,
#    che e' del `prova2` **del contenitore**: sono due utenti diversi con lo
#    stesso nome, e le due parole si somigliano abbastanza da far perdere
#    un'ora (`banchi/06-b38-tela.sh`).  ⛔ E si prende **dalla riga di
#    `chpasswd`**, non dalla prima che combacia: senza `grep chpasswd` la
#    prima occorrenza di `prova2:` in quel file e' `for u in prova:1001
#    prova2:1002`, e il banco userebbe **`1002`** come parola — cinque
#    `RESPINTO` e il ban;
#  · la parola **non va mai in `argv`** (si vede in `ps`): si passa con
#    `--parola-file` su un file `0600`.  E' il difetto **D12**;
#  · ⚠ ogni tentativo sbagliato conta, e al **quarto** scatta il ban di 12 ore.
#    Non si indovina: se la riga non si trova, ci si ferma.
#
# ---------------------------------------------------------------------------
# ⛔ E SE LA CATTURA NON C'E' ANCORA — «non c'e'» non e' «non funziona»
# ---------------------------------------------------------------------------
#
# Quando questo banco e' stato scritto il prodotto **non aveva** il sink nella
# sessione ne' la cattura del monitor (`fasi/07-audio-e-appunti.md` §4.2: *«quel
# che ancora NON c'e', ed e' meta' della catena»*).  Un banco che desse ROSSO in
# quel caso accuserebbe il prodotto di un difetto che non ha: sarebbe un rosso
# su codice che non e' stato ancora scritto.
#
# ⭐ **E il cancello e' stato visto scattare in tutt'e due i versi nella stessa
# mattinata**, il che e' il miglior controllo che potesse avere:
#
#   | `[M]` 17 ago 2026 | «support.null-audio-sink» | «monitor.channel-volumes» | «libopus» |
#   |---|---|---|---|
#   | binario delle 09:25 (prima di `suono.c`) | **0** | **0** | 2 |
#   | binario delle 09:56 (`suono.c` entrato)  | **1** | **1** | 2 |
#
# ⇒ Il primo dava «CANCELLO CHIUSO» e uscita **4**; il secondo «CANCELLO
#   APERTO».  ⚠ E `libopus` **2 in tutt'e due**: e' il controllo positivo della
#   ricerca, e dice che a cambiare e' stato il binario, non lo strumento.
#
# ⇒ Il **cancello** (passo 3) guarda due cose, e le distingue:
#
#   | binario | sink nel grafo | che cosa dice il banco | uscita |
#   |---|---|---|---|
#   | non nomina il sink | assente | *«il prodotto non ha ancora la cattura dell'audio»* | **4** |
#   | lo nomina | assente | ⛔ **ROSSO vero**: il codice c'e' e il sink non nasce | 1 |
#   | non lo nomina | presente | ⚠ anomalia: qualcuno l'ha creato a mano | prosegue, dichiarando |
#   | lo nomina | presente | ⭐ si misura | — |
#
# ⚠ E il cancello ha il **suo** controllo positivo, che costa una riga:
#   `LEZIONI.md` §1.9 regola 2 — *«questo strumento sa trovare qualcosa che
#   c'e' di sicuro?»*  Si cerca anche **`libopus`**, che nel binario **deve**
#   esserci (`src/audio.c` lo chiede per nome).  Se non lo trova, non e' il
#   sink che manca: e' la ricerca che non funziona.
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA E' MISURATO E CHE COSA NO — al 17 agosto 2026, senza indulgenza
# ---------------------------------------------------------------------------
#
# `[M]` **girato davvero**:
#   · il **giudizio**, su registrazioni vere del monitor di un sink: cinque
#     giri con l'atteso dichiarato prima, e il banco li ha fatti combaciare
#     tutti e cinque (uscita 0).  Rifatto sul sink **senza**
#     `monitor.channel-volumes`: **uscita 1**, ROSSO(VOLUME-NON-ARRIVA) sul
#     giro del 25 % e su quello del muto;
#   · i **quattro codici d'uscita**, esercitati uno per uno: 0, 1, 2 (file
#     vuoto, e finestra non intera), 3 (banco cieco: un difetto innestato che
#     non viene visto);
#   · il **cancello**, in tutt'e due i versi (la tabella qui sopra);
#   · **M2 e la lettura del volume**, contro il sink **vero** del prodotto
#     nella sessione viva di `prova2`: `{"sink_nome":"remotix","sink_id":59,
#     "monitor_channel_volumes":true,"channel_volumes":[1.0,1.0],"mute":false,
#     "legami_in_ingresso":0}`;
#   · **M3**, sul portatile e dentro la sessione di `prova2`;
#   · gli **attrezzi**: `pw-play`, `pw-dump`, `wpctl`, `python3`, `setpriv`,
#     `awk` ci sono; ⛔ **`ffmpeg` e `bc` NO** (fuori dal contenitore), e il
#     copione e' scritto per farne a meno.
#
# `[?]` **scritto e non girato**, e va detto:
#   · **il giro intero contro il prodotto** — cliente, datagram, JSONL.  Il
#     giorno in cui e' stato scritto, `prova2` era gia' servito dal server
#     della **7710**, e `SPECIFICHE.md` §5.1 ne ammette **una sola** sessione
#     per utente: strappargliela avrebbe fermato il banco di un altro.  ⇒ Il
#     passo `terreno` lo **rifiuta e lo dichiara**, invece di provarci;
#   · di conseguenza **M1** (il marcatore del cliente) e' `[?]`: il file di
#     `--segnale` e' quello che `01-b3-cliente.py` gia' scrive da altri banchi,
#     ma qui non lo si e' visto arrivare;
#   · il **ritmo** dell'audio vero: si riferisce, non si giudica — nessuno ha
#     ancora misurato che cadenza dia PipeWire su questa catena.
#
# ---------------------------------------------------------------------------
# I CODICI D'USCITA, e sono cinque perche' i casi sono cinque
# ---------------------------------------------------------------------------
#
#   0  ⭐ ogni giro ha fatto quel che era dichiarato prima
#   1  ⛔ il PRODOTTO e' rosso
#   2  ⚠  il TERRENO o il BANCO: non ho misurato (`CODER.md` §3.10)
#   3  ⛔ il BANCO E' CIECO: un difetto innestato non e' stato visto
#   4  ⏳ **il prodotto non ha ancora la cattura dell'audio** — non e' un
#         difetto, e' un pezzo che non c'e'
#
# ---------------------------------------------------------------------------
# COME SI USA
# ---------------------------------------------------------------------------
#
#   dal portatile (l'orchestratore):
#       bash banchi/07-b43-audio-vero.sh              tutto il giro
#       bash banchi/07-b43-audio-vero.sh --solo-cancello
#       bash banchi/07-b43-audio-vero.sh --resta-acceso
#       bash banchi/07-b43-audio-vero.sh --spegni
#
#   sulla macchina di prova (lo esegue l'orchestratore, DA ROOT):
#       bash .../banchi/07-b43-audio-vero.sh --sul-server <passo>
#
# ⚠ Se un giorno il prodotto vorra' un'opzione per accendere la cattura, la si
#   passa **senza toccare questo file**:  OPZIONI_SERVER='--audio-sessione' bash …
# ===========================================================================
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7720}
UTENTE=${UTENTE:-prova2}
UID_B=${UID_B:-1002}
SINK=${SINK:-remotix}          # `v1/remotix-c/src/suono.c`: `#define NOME_SINK "remotix"`
ALBERO=${ALBERO:-/media/REMOTIX/src/07-vero-src}
LAV=${LAV:-/media/REMOTIX/tmp/07-vero}
DENTRO_ALB=${DENTRO_ALB:-/srv/src/07-vero-src}
DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/07-vero}
UNITA=${UNITA:-remotix-$PORTA}
OPZIONI_SERVER=${OPZIONI_SERVER:-}

# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, e non si toccano mai.
#    Se una sparisce mentre giro, l'ho rotta io.
VICINE="7448 7700 7710"

# La scena, in numeri, e dichiarata qui una volta sola.
HZ_ATTESO=${HZ_ATTESO:-440}
HZ_SBAGLIATO=${HZ_SBAGLIATO:-660}
AMPIEZZA=${AMPIEZZA:-0.5}
# ⭐ Un seno di ampiezza A ha RMS A/√2.  0,5/√2 = 0,35355 — ed e' lo stesso
#    numero che `07-b40` ha usato per certificare il giudice (RMS attesa
#    0,3536), quindi i due banchi si possono confrontare.
RMS_BASE=${RMS_BASE:-0.3536}
SECONDI=${SECONDI:-16}         # quanto resta attaccato il cliente
FINESTRA=${FINESTRA:-2}        # ⛔ INTERO di secondi: vedi 07-b43-giudizio.py
MARGINE=${MARGINE:-2}          # quanto si scarta fra M3 e l'inizio della finestra

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SULLA MACCHINA DI PROVA, DA ROOT
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--sul-server" ]; then
	PASSO=${2:-stato}
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--sul-server» va eseguito DA ROOT"; exit 2; }
	# ⚠ La cartella di lavoro si fa QUI, prima di ogni passo: il primo giro ha
	#   trovato `grafo` che scriveva in una cartella che nessuno aveva ancora
	#   creato, e il messaggio era «No such file or directory» — cioe' un
	#   difetto di banco travestito da «non riesco a leggere il grafo».
	mkdir -p "$LAV" 2>/dev/null

	# ⛔ Tutto quel che va fatto DENTRO la sessione dell'utente passa di qui:
	#    uid, gid, e l'ambiente **composto da zero** (`CODER.md` §4.5 — «chi
	#    avvia una sessione le regala tutto il proprio ambiente, comprese le
	#    variabili che non c'entrano»).  La forma e' quella di
	#    `06-b35-terreno.sh`, e non si reinventa.
	#
	# ⚠ E una trappola pagata oggi provando la scena: `come_utente` e' una
	#   **funzione di shell**, quindi `timeout 8 come_utente pw-cli …` NON
	#   funziona — `timeout` cerca un eseguibile e esce **127**.  ⛔ E un 127
	#   dentro una sostituzione di comando ha la stessa faccia di «il comando
	#   non ha trovato niente»: ho creduto per due giri che il sink non
	#   nascesse, mentre non era mai stato chiesto.  ⇒ Il tetto si mette
	#   DENTRO: `come_utente timeout 8 pw-cli …`.
	come_utente() {
		setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
			env -i \
			HOME="/home/$UTENTE" USER="$UTENTE" LANG=C.UTF-8 \
			PATH=/usr/local/bin:/usr/bin:/bin \
			XDG_RUNTIME_DIR="/run/user/$UID_B" \
			DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_B/bus" \
			"$@"
	}
	# ⛔⭐ SI ZITTISCE LA SCENA, E SI VERIFICA CHE SIA ZITTA.
	#
	#     `[M]` 17 agosto 2026: il giro «2-silenzio» misurava **440 Hz a
	#     0,3535** — cioe' il tono a pieno volume dove non doveva suonare
	#     niente, e il banco si dichiarava CIECO.  ⛔ La causa: `kill "$PP"`
	#     uccide l'**involucro** (`setpriv`), non `pw-play`, che sopravvive e
	#     continua a suonare **dentro il giro dopo**.
	#
	# ⚠ E lo stato che resta da un giro all'altro e' la trappola che
	#   `LEZIONI.md` §2.3-quinquies nomina per la clipboard: «quel che resta
	#   dal giro prima va svuotato all'inizio».  Vale per ogni scena condivisa,
	#   e il suono e' una scena condivisa.
	#
	# ⛔ Non basta uccidere: si CONTROLLA dal grafo che i legami in ingresso al
	#    sink siano zero.  «Ho ucciso» e «non suona piu' nessuno» sono due
	#    fatti diversi, e solo il secondo e' quello che serve al giro dopo.
	zittisci() {
		local i legami
		pkill -u "$UID_B" -x pw-play 2>/dev/null || true
		for i in $(seq 1 40); do
			legami=$(come_utente pw-dump 2>/dev/null | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: print(-1); raise SystemExit
n=0
for o in d:
    if o.get('type','').endswith('Link'):
        p=(o.get('info') or {}).get('props') or {}
        if p.get('link.input.node') == $1: n+=1
print(n)
" 2>/dev/null || echo -1)
			[ "$legami" = "0" ] && return 0
			sleep 0.25
		done
		return 1
	}

	# Il contenitore: ci sta `aioquic`, che sull'host non c'e'.  ⚠ Siamo gia'
	# root, quindi il `sudo -n true` interno di `enter.sh` passa senza parola.
	dentro() { bash /media/REMOTIX/enter.sh --root "$1"; }

	vicini() {
		local r="" p
		for p in $VICINE; do r="$r$p:$(ss -tuln 2>/dev/null | grep -c ":$p\b") "; done
		printf '%s— ascoltatori NON miei (si contano, non si toccano)' "$r"
	}

	# ── Il grafo di PipeWire, letto DENTRO la sessione ────────────────────
	#
	# ⛔ `pw-dump` deve girare come l'utente della sessione (il socket sta in
	#    `/run/user/<uid>`), ma il filtro puo' girare da root.  ⚠ Si passa per
	#    un file invece che per una pipe: il filtro vuole lo `stdin` per il
	#    proprio testo, e una pipe glielo toglierebbe.
	grafo() # $1 = file dove scrivere la risposta
	{
		local fuori=$1 dump=$LAV/.pwdump.json
		: > "$dump"
		come_utente pw-dump > "$dump" 2>/dev/null
		# ⛔ Una lettura NEGATA non e' una lettura che dice zero (`CODER.md`
		#    §3.10): un dump vuoto si dichiara, non si interpreta.
		if [ ! -s "$dump" ]; then
			printf '{"errore":"pw-dump non ha prodotto niente dentro la sessione di %s: o PipeWire non gira, o il runtime dir non e leggibile — NON e la stessa cosa di «il sink non ce»"}\n' \
				"$UTENTE" > "$fuori"
			return 1
		fi
		SINK="$SINK" python3 - "$dump" > "$fuori" <<'FINE'
import json, os, sys
nome = os.environ["SINK"]
d = json.load(open(sys.argv[1]))
r = {"sink_nome": nome, "sink_id": None, "monitor_channel_volumes": None,
     "channel_volumes": None, "mute": None, "legami_in_ingresso": 0,
     "nodi_audio_sink": []}
for o in d:
    info = o.get("info") or {}
    p = info.get("props") or {}
    if p.get("media.class") == "Audio/Sink":
        r["nodi_audio_sink"].append(p.get("node.name"))
    if p.get("node.name") == nome and p.get("media.class") == "Audio/Sink":
        r["sink_id"] = o["id"]
        mcv = p.get("monitor.channel-volumes")
        r["monitor_channel_volumes"] = mcv
        for s in (info.get("params") or {}).get("Props", []):
            if "channelVolumes" in s:
                r["channel_volumes"] = s.get("channelVolumes")
                r["mute"] = s.get("mute")
                break
for o in d:
    if str(o.get("type", "")).endswith("Link"):
        p = (o.get("info") or {}).get("props") or {}
        if r["sink_id"] is not None and p.get("link.input.node") == r["sink_id"]:
            r["legami_in_ingresso"] += 1
print(json.dumps(r, ensure_ascii=False))
FINE
		return 0
	}

	leggi() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],''))" "$1" "$2" 2>/dev/null; }

	# ⛔ I conti si fanno con `awk`, NON con `bc`: `[M]` 17 agosto 2026, sulla
	#    macchina di prova **`bc` non c'e'** (`awk` si).  ⚠ E un `bc` mancante
	#    non da' un errore utile dentro una sostituzione di comando: da' una
	#    stringa vuota, e il confronto dopo diventa vero o falso a caso — cioe'
	#    esattamente la forma di `LEZIONI.md` §2.3, «il banco boccia il codice
	#    giusto».  ⇒ Si verifica che l'attrezzo esista prima di dipenderne.
	conto()  { awk "BEGIN{printf \"%.1f\", $1}"; }
	minore() { awk "BEGIN{exit !($1 < $2)}"; }

	attendi_file() # $1 file, $2 secondi di tetto
	{
		local i=0
		while [ "$i" -lt $(( ${2} * 10 )) ]; do
			[ -f "$1" ] && return 0
			sleep 0.1; i=$((i+1))
		done
		return 1
	}

	case "$PASSO" in
	# ───────────────────────────────────────────────────────────────────
	cancello)
		# ⛔ IL CANCELLO: «non c'e' ancora» non deve avere la faccia di «non
		#    funziona».  Si guarda il BINARIO, che e' l'unica cosa che si
		#    puo' guardare prima di accendere qualsiasi cosa.
		log "Il cancello — il prodotto ha la cattura del suono della sessione?"
		[ -x "$ALBERO/src/remotix" ] || { ko "⛔ «$ALBERO/src/remotix» non c'e'"; exit 2; }
		inf "binario: $(stat -c '%y  %s byte' "$ALBERO/src/remotix")"
		# ⚠ `strings` NON c'e' su questa macchina (`[M]` 17 ago 2026: binutils
		#   non installato), e `grep -a` fa lo stesso mestiere senza
		#   dipendenze nuove.  ⛔ E si stampa il DENOMINATORE di ogni ricerca.
		A=$(grep -ac -- 'support.null-audio-sink' "$ALBERO/src/remotix")
		B=$(grep -ac -- 'monitor.channel-volumes' "$ALBERO/src/remotix")
		C=$(grep -ac -- 'libopus' "$ALBERO/src/remotix")
		inf "«support.null-audio-sink» : $A righe   (il sink di v1)"
		inf "«monitor.channel-volumes» : $B righe   (la cura di §kde §10.5)"
		inf "«libopus»                 : $C righe   ⭐ controllo POSITIVO della ricerca"
		if [ "$C" -eq 0 ]; then
			ko "⛔ la ricerca non trova nemmeno «libopus», che nel binario DEVE"
			ko "   esserci (src/audio.c lo chiede per nome): non e' il sink che"
			ko "   manca, e' lo STRUMENTO che non funziona.  Non concludo niente."
			exit 2
		fi
		if [ "$A" -eq 0 ] && [ "$B" -eq 0 ]; then
			printf 'CANCELLO CHIUSO\n'
			exit 4
		fi
		printf 'CANCELLO APERTO\n'
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	grafo)
		# ⭐ Una lettura SOLA del grafo, senza toccare niente: serve a
		#    guardare la sessione di qualcun altro senza entrarci dentro, e a
		#    rispondere alla domanda che precede ogni giro — *«il sink c'e'?»*
		log "Il grafo di PipeWire nella sessione di $UTENTE"
		if grafo "$LAV/grafo-ora.json"; then
			cat "$LAV/grafo-ora.json"
		else
			cat "$LAV/grafo-ora.json"; exit 2
		fi
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	terreno)
		log "Il terreno — si VERIFICA, non si spera"
		inf "$(vicini)"
		inf "carico: $(uptime | sed 's/.*average/media/')"
		inf "orologio di questa macchina: $(date)   ⚠ non e' quello del portatile"
		[ -f /etc/pam.d/remotix ] || { ko "⛔ manca /etc/pam.d/remotix: PAM direbbe sempre di no"; exit 2; }
		n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
		[ "$n" -eq 0 ] || { ko "⛔ la porta $PORTA e' gia' occupata: non si accende sopra"; exit 2; }
		id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente $UTENTE non esiste"; exit 2; }
		[ -d "/run/user/$UID_B" ] || { ko "⛔ /run/user/$UID_B non c'e': senza linger la sessione non ha dove vivere"; exit 2; }
		# ⛔⛔ E LA COSA CHE FA SEMBRARE ROTTO IL PRODOTTO: `SPECIFICHE.md` §5.1
		#     dice **una sola sessione grafica per utente**.  Se `prova2` e'
		#     gia' in mano al server di un altro banco, questo qui prendera'
		#     `CONGEDO(GIA_ATTIVA_REMOTA)` — che e' l'invariante I2 che
		#     funziona, non un difetto.  ⇒ Si guarda PRIMA, e si dice chi c'e'.
		ALTRI=$(pgrep -a -f -- "--figlio-interno $UTENTE" 2>/dev/null | grep -v "$LAV" || true)
		if [ -n "$ALTRI" ]; then
			ko "⚠ $UTENTE e' GIA' servito da un altro server:"
			printf '%s\n' "$ALTRI" | sed 's/^/        /'
			ko "   ⛔ Non tocco niente e non provo a strapparglielo (I2)."
			ko "   ⇒ O si aspetta che quel banco finisca, o si lancia questo con"
			ko "     UTENTE=<un altro> UID_B=<il suo uid>."
			exit 2
		fi
		ok "porta $PORTA libera · PAM a posto · $UTENTE libero"
		# Gli attrezzi della scena: si verificano PRIMA di dipenderne.
		# ⛔ «Verifica che l'attrezzo esista PRIMA di dipenderne»: e' la lezione
		#    di `LEZIONI.md` §1.1 (il `weston-simple-egl` che non era
		#    installato) e §2.5-bis (le dipendenze messe a mano che spariscono
		#    al primo riavvio).  ⚠ E si dichiara che cosa si e' trovato.
		#    `[M]` 17 ago 2026 su questa macchina: **`ffmpeg` non c'e'** fuori
		#    dal contenitore, e **`bc` nemmeno** — per questo il tono lo scrive
		#    `python3` e i conti li fa `awk`.
		MANCA=""
		for t in pw-play pw-dump wpctl python3 setpriv awk; do
			command -v "$t" >/dev/null 2>&1 || MANCA="$MANCA $t"
		done
		[ -z "$MANCA" ] || { ko "⛔ attrezzi mancanti sull'host:$MANCA"; exit 2; }
		ok "attrezzi della scena: pw-play, pw-dump, wpctl, python3, setpriv, awk"
		inf "PipeWire di $UTENTE: $(come_utente pw-cli info 0 2>/dev/null | head -1 || echo '⚠ non risponde')"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	accendi)
		log "Il server del banco, sulla $PORTA — unita' $UNITA.service"
		inf "$(vicini)"
		mkdir -p "$LAV/certificati" "$LAV/rilievo"; chmod 1777 "$LAV/rilievo"
		chmod 755 "$LAV"   # ⚠ `prova2` deve poter leggere il file del tono
		: > "$LAV/registro.log"

		B2=/media/REMOTIX/src/b2
		export LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
		# ⛔ La trappola 1 di `riavvia-7700.sh`: senza questo controllo il
		#    binario prende la ngtcp2 di **sistema**, parte benissimo e ABORTA
		#    al primo che si collega.  Si verifica PRIMA di accendere.
		MANCA=$(ldd "$ALBERO/src/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
		if [ "$MANCA" != "0" ]; then
			ko "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da $B2 —"
			ldd "$ALBERO/src/remotix" | grep -E 'ngtcp2|nghttp3' | sed 's/^/        /'
			exit 2
		fi
		ok "ldd: ngtcp2 e nghttp3 vengono da $B2"

		systemctl stop "$UNITA.service" 2>/dev/null
		systemctl reset-failed "$UNITA.service" 2>/dev/null
		i=0
		while ss -uln 2>/dev/null | grep -q ":$PORTA " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

		# ⛔ Parte come UNITA' DI SISTEMA, non da questa ssh: `setsid` stacca
		#    dal terminale ma NON dalla sessione di logind, e da dentro una
		#    ssh `pam_systemd` non ne crea una seconda per il figlio —
		#    `/run/user/<uid>` non esiste e il sintomo e' «il desktop non
		#    parte».  E' la trappola 4 di `riavvia-7700.sh`, e la stessa
		#    ragione per cui `07-b41-accendi.sh` fa cosi'.
		# ⭐ `--parlantina`: il figlio senza parlantina TACE IN SILENZIO, e ha
		#    gia' mentito nella direzione peggiore.
		# ⛔ E **niente `--audio-prova`**: e' il tono che fabbrica il SERVER, ed
		#    e' esattamente quel che questo banco NON deve sentire.  Se lo
		#    sentisse, sarebbe verde senza che la sessione suoni.
		# shellcheck disable=SC2086
		systemd-run \
			--unit="$UNITA" --collect --description="REMOTIX_V2, banco 07-b43 (audio VERO)" \
			--working-directory="$ALBERO/src" \
			--setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
			--property=StandardOutput=append:$LAV/registro.log \
			--property=StandardError=append:$LAV/registro.log \
			--property=KillMode=mixed \
			"$ALBERO/src/remotix" \
			--indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
			--certificati "$LAV/certificati" \
			--pagina "$ALBERO/src/pagina.html" \
			--ban-file "$LAV/ban" \
			--comando-socket "$LAV/comando.sock" \
			--rilievo "$LAV/rilievo" \
			$OPZIONI_SERVER \
			--parlantina >/dev/null || { ko "⛔ systemd-run ha rifiutato"; exit 2; }

		i=0; PID=0
		while [ $i -lt 50 ]; do
			PID=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
			[ "$PID" != "0" ] && [ -n "$PID" ] && break
			i=$((i+1)); sleep 0.1
		done
		if [ "$PID" = "0" ] || [ -z "$PID" ]; then
			ko "⛔ il server non e' partito — le ultime righe:"
			tail -20 "$LAV/registro.log" | sed 's/^/        /'
			exit 2
		fi
		ok "server $PID sulla porta $PORTA"
		[ -n "$OPZIONI_SERVER" ] && inf "⚠ opzioni in piu' passate dal lanciatore: $OPZIONI_SERVER"
		inf "$(vicini)"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	parola)
		# ⛔ La parola si LEGGE dalla riga di `chpasswd`, e finisce in un file
		#    0600 — mai in un argv (D12).  La forma e' identica a quella di
		#    `06-b38-tela.sh`, e non si reinventa: reinventarla e' costato un
		#    ban di 12 ore a chi l'ha fatto.
		P=$(grep 'chpasswd' "$ALBERO/src/provisiona.sh" \
		    | grep -o "$UTENTE:[A-Za-z0-9._-]*" | head -1 | cut -d: -f2)
		if [ -z "$P" ]; then
			ko "⛔ non ho trovato la parola di $UTENTE nella riga chpasswd di"
			ko "   $ALBERO/src/provisiona.sh — e NON provo a indovinarla: al"
			ko "   quarto tentativo sbagliato scatta il ban di 12 ore (§4.4-bis)"
			exit 2
		fi
		mkdir -p "$LAV"
		( umask 077; : > "$LAV/parola" ) && chmod 600 "$LAV/parola" || {
			ko "⛔ non si scrive $LAV/parola"; exit 2; }
		printf '%s\n' "$P" > "$LAV/parola"
		unset P
		ok "la parola di $UTENTE sta in un file 0600 — mai in un argv (D12)"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	tono)
		# Il file del tono, fabbricato qui: ⭐ cosi' l'ampiezza e' NOTA, e
		# l'RMS atteso non e' una stima ma un conto (A/√2).
		# ⛔ `ffmpeg` NON c'e' sull'host (`[M]` 17 ago 2026: c'e' solo dentro il
		#    contenitore, e la sessione grafica sta FUORI dal contenitore).
		#    ⇒ Il tono lo scrive `python3` col modulo `wave` della libreria
		#    standard, e lo suona `pw-play`, che c'e' (`[M]` PipeWire 1.4.2).
		HZ=${HZ:-440}; SEC=${SEC:-40}
		mkdir -p "$LAV"
		HZ="$HZ" SEC="$SEC" AMP="$AMPIEZZA" python3 - "$LAV/tono-$HZ.wav" <<'FINE'
import math, os, struct, sys, wave
hz = int(os.environ["HZ"]); sec = int(os.environ["SEC"]); amp = float(os.environ["AMP"])
w = wave.open(sys.argv[1], "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
d = bytearray()
for n in range(48000 * sec):
    v = int(amp * math.sin(2 * math.pi * hz * n / 48000) * 32767)
    d += struct.pack("<hh", v, v)
w.writeframes(bytes(d)); w.close()
FINE
		chmod 644 "$LAV/tono-$HZ.wav"
		ok "tono $HZ Hz, ampiezza $AMPIEZZA, $SEC s: $(stat -c %s "$LAV/tono-$HZ.wav") byte"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	giro)
		# =============================================================
		# UN GIRO: la scena, i tre marcatori, la presa.
		# =============================================================
		NOME=${NOME:?serve NOME}
		SUONA=${SUONA:-si}          # si | no
		HZ=${HZ:-440}
		VOLUME=${VOLUME:-pieno}     # pieno | 0.25 | muto
		ROSSO_ATTESO=${ROSSO_ATTESO:-}
		RMS_DA_GIRO=${RMS_DA_GIRO:-}
		DESCRIZIONE=${DESCRIZIONE:-}
		ATTESO_A_PAROLE=${ATTESO_A_PAROLE:-}

		log "GIRO «$NOME»"
		inf "$(vicini)"

		# ⚠ QUEL CHE RESTA DAL GIRO PRIMA SI SVUOTA — `LEZIONI.md`
		#   §2.3-quinquies, il corollario: quel che avanza dal giro
		#   precedente viene riletto e **sembra un risultato**.
		rm -f "$LAV/$NOME.jsonl" "$LAV/$NOME.segnale" "$LAV/$NOME.txt" \
		      "$LAV/$NOME.stato.json"

		# ── ⛔ L'ATTESO SI DICHIARA PRIMA, e si scrive su disco PRIMA di
		#    allestire la scena (regola B0.4 di `06-b38-tela.sh`): e' l'unica
		#    cosa che distingue una misura da una spiegazione di quel che e'
		#    successo.
		NOME="$NOME" HZ="$HZ" FINESTRA="$FINESTRA" RMS_BASE="$RMS_BASE" \
		ROSSO_ATTESO="$ROSSO_ATTESO" RMS_DA_GIRO="$RMS_DA_GIRO" \
		DESCRIZIONE="$DESCRIZIONE" ATTESO_A_PAROLE="$ATTESO_A_PAROLE" \
		HZ_ATTESO="$HZ_ATTESO" python3 - "$LAV/$NOME.atteso.json" <<'FINE'
import json, os, sys
a = {
    "nome": os.environ["NOME"],
    "descrizione": os.environ["DESCRIZIONE"],
    "atteso_a_parole": os.environ["ATTESO_A_PAROLE"],
    # ⛔ `hz` e' quel che IL BANCO si aspetta di sentire, non quel che la
    #    scena suona: nel giro della frequenza sbagliata sono due numeri
    #    diversi, ed e' precisamente il difetto innestato.
    "hz": int(os.environ["HZ_ATTESO"]),
    "finestra_s": int(os.environ["FINESTRA"]),
    "rms_base": float(os.environ["RMS_BASE"]),
    "rms_da_giro": os.environ["RMS_DA_GIRO"] or None,
    "scala_col_guadagno": True,
    "rosso_atteso": os.environ["ROSSO_ATTESO"] or None,
}
json.dump(a, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
FINE
		inf "⛔ ATTESO, scritto PRIMA: $ATTESO_A_PAROLE"

		# ── Il cliente parte per primo: e' lui che apre la sessione, ed e'
		#    dentro la sessione che nascera' il sink.
		CMD="python3 -u $DENTRO_ALB/banchi/01-b3-cliente.py \
--indirizzo $IND --porta $PORTA --utente $UTENTE \
--parola-file $DENTRO_LAV/parola \
--audio-codec pcm \
--audio-scrivi $DENTRO_LAV/$NOME.jsonl \
--segnale $DENTRO_LAV/$NOME.segnale \
--resta $SECONDI"
		# ⛔ `--audio-codec pcm` NON e' un aggiramento: §4.3 rende il PCM la
		#    base obbligatoria ai due capi, e i pacchetti Opus qui non si
		#    giudicano — li giudica il BROWSER, che ha il decodificatore
		#    dell'utente (forma d'errore E10, e lo dice gia' `07-b42`).
		( dentro "$CMD" > "$LAV/$NOME.txt" 2>&1 ) &
		CLI=$!
		T0=$(date +%s.%N)

		# ── M1 · il cliente ha aperto la sessione ─────────────────────
		if ! attendi_file "$LAV/$NOME.segnale" 60; then
			ko "⛔ M1 non e' arrivato in 60 s: il cliente non ha aperto la sessione."
			ko "   ⚠ E NON e' «l'audio non arriva»: e' «la scena non e' stata"
			ko "     allestita».  Le ultime righe del cliente:"
			tail -20 "$LAV/$NOME.txt" 2>/dev/null | sed 's/^/        /'
			kill "$CLI" 2>/dev/null; wait "$CLI" 2>/dev/null
			exit 2
		fi
		T1=$(date +%s.%N)
		ok "M1 · sessione aperta dopo $(conto "$T1 - $T0") s"

		# ── M2 · il sink esiste nel grafo ─────────────────────────────
		#
		# ⚠ Il sink puo' comparire qualche decimo DOPO la sessione: si
		#   aspetta, ma con un tetto e con un esito suo.
		g=0; SINK_ID=""
		while [ $g -lt 100 ]; do
			grafo "$LAV/$NOME.grafo.json"
			SINK_ID=$(leggi "$LAV/$NOME.grafo.json" sink_id)
			[ -n "$SINK_ID" ] && [ "$SINK_ID" != "None" ] && break
			sleep 0.2; g=$((g+1))
		done
		if [ -z "$SINK_ID" ] || [ "$SINK_ID" = "None" ]; then
			ko "⛔ M2: nessun sink «$SINK» nel grafo di $UTENTE dopo 20 s."
			inf "quel che c'e': $(leggi "$LAV/$NOME.grafo.json" nodi_audio_sink)"
			inf "$(cat "$LAV/$NOME.grafo.json" 2>/dev/null)"
			ko "   ⚠ Questo e' l'esito che distingue «non c'e' ancora» da «non"
			ko "     funziona»: lo decide il CANCELLO, che ha gia' guardato il"
			ko "     binario.  Qui si registra il fatto e si va avanti."
		else
			ok "M2 · sink «$SINK» id $SINK_ID · $(cat "$LAV/$NOME.grafo.json")"
		fi

		# ── Il volume del sink, e si VERIFICA che abbia obbedito ──────
		#
		# ⛔ `CODER.md` §3.9: si chiede per nome e si verifica.  Qui si
		#    rilegge `channelVolumes` DAL GRAFO, e quel numero e' l'atteso
		#    del giudice — non una traduzione fatta da noi della curva del
		#    cursore.  `[M]` `wpctl set-volume 0.25` scrive **0,015625**
		#    (= 0,25³, la curva cubica di PulseAudio).
		if [ -n "$SINK_ID" ] && [ "$SINK_ID" != "None" ]; then
			case "$VOLUME" in
			muto)  come_utente wpctl set-mute "$SINK_ID" 1 2>/dev/null ;;
			pieno) come_utente wpctl set-mute "$SINK_ID" 0 2>/dev/null
			       come_utente wpctl set-volume "$SINK_ID" 1.0 2>/dev/null ;;
			*)     come_utente wpctl set-mute "$SINK_ID" 0 2>/dev/null
			       come_utente wpctl set-volume "$SINK_ID" "$VOLUME" 2>/dev/null ;;
			esac
			sleep 0.5
			grafo "$LAV/$NOME.grafo.json"
			inf "volume chiesto «$VOLUME» · il grafo dice: channelVolumes=$(leggi "$LAV/$NOME.grafo.json" channel_volumes) mute=$(leggi "$LAV/$NOME.grafo.json" mute)"
		fi

		# ── M3 · il tono suona DAVVERO dentro il sink ─────────────────
		PP=0
		TONO_VIVO=false
		if [ "$SUONA" = si ]; then
			come_utente pw-play --target "$SINK" "$LAV/tono-$HZ.wav" \
				> "$LAV/$NOME.play.txt" 2>&1 &
			PP=$!
			g=0; LEG=0
			while [ $g -lt 100 ]; do
				grafo "$LAV/$NOME.grafo.json"
				LEG=$(leggi "$LAV/$NOME.grafo.json" legami_in_ingresso)
				[ "${LEG:-0}" -gt 0 ] 2>/dev/null && break
				kill -0 "$PP" 2>/dev/null || break
				sleep 0.2; g=$((g+1))
			done
			if [ "${LEG:-0}" -gt 0 ] 2>/dev/null; then
				ok "M3 · $LEG legami in ingresso al sink: il tono STA suonando"
				ok "     ⭐ e non e' «ho lanciato pw-play»: e' il grafo che lo dice"
			else
				ko "⛔ M3 non e' arrivato: `pw-play` non risulta collegato al sink."
				tail -5 "$LAV/$NOME.play.txt" 2>/dev/null | sed 's/^/        /'
			fi
		else
			# ⭐ Il giro del silenzio ha il suo marcatore, ed e' il contrario:
			#    si VERIFICA che nessuno stia suonando, invece di darlo per
			#    scontato.  Un residuo del giro prima darebbe un verde falso.
			grafo "$LAV/$NOME.grafo.json"
			LEG=$(leggi "$LAV/$NOME.grafo.json" legami_in_ingresso)
			if [ "${LEG:-0}" -eq 0 ] 2>/dev/null; then
				ok "M3 (rovesciato) · 0 legami in ingresso: nessuno sta suonando"
			else
				ko "⚠ ci sono $LEG legami in ingresso al sink e questo giro"
				ko "  dovrebbe essere MUTO: qualcuno del giro prima e' rimasto"
			fi
		fi
		T3=$(date +%s.%N)

		# ── La finestra da giudicare SI CALCOLA, non si spera ─────────
		#
		# ⛔ E' il cuore della regola (b): la finestra utile e' quel che resta
		#    fra M3 e la fine della presa, meno un margine.  Se non ci sta,
		#    lo si DICE — un giudizio dato su una finestra che non e' coperta
		#    dal tono sarebbe un rosso su codice giusto.
		RESTA=$(conto "$SECONDI - ($T3 - $T0) - $MARGINE")
		if minore "$RESTA" "$FINESTRA"; then
			ko "⚠ fra M3 e la fine della presa restano $RESTA s, meno della"
			ko "  finestra di $FINESTRA s: alzare SECONDI (ora $SECONDI)."
			ko "  ⛔ Non si giudica su una finestra che il tono non copre: sarebbe"
			ko "    un rosso su codice giusto (`LEZIONI.md` §2.3)."
		else
			ok "finestra: $FINESTRA s di coda dentro $RESTA s coperti dal tono"
		fi

		# ── Si aspetta il cliente: e' lui che scrive il JSONL, all'uscita ──
		wait "$CLI"; USCITA=$?
		if [ "$PP" != 0 ] && kill -0 "$PP" 2>/dev/null; then
			TONO_VIVO=true
			kill "$PP" 2>/dev/null; wait "$PP" 2>/dev/null
		fi
		# ⛔ E si zittisce DAVVERO, verificandolo dal grafo: `kill` sull'involucro
		#    lasciava vivo `pw-play`, che suonava dentro il giro dopo.
		if [ -n "$SINK_ID" ] && [ "$SINK_ID" != "None" ]; then
			if zittisci "$SINK_ID"; then
				inf "scena zittita: 0 legami in ingresso al sink"
			else
				ko "⛔ la scena NON si zittisce: restano legami in ingresso al "
				ko "   sink.  Il giro dopo misurerebbe il tono di questo."
			fi
		fi
		# Si rimette il sink com'era, o il giro dopo parte da uno stato
		# invisibile ereditato da questo.
		if [ -n "$SINK_ID" ] && [ "$SINK_ID" != "None" ]; then
			come_utente wpctl set-mute "$SINK_ID" 0 2>/dev/null
			come_utente wpctl set-volume "$SINK_ID" 1.0 2>/dev/null
		fi

		inf "il cliente esce $USCITA   (0 = e' rimasto attaccato · 4 = caduta)"
		sed 's/^/    | /' "$LAV/$NOME.txt" 2>/dev/null | tail -14

		# ── Lo stato della scena, scritto ACCANTO alla misura ─────────
		#
		# ⛔ `LEZIONI.md` §2.0: «un banco che risponde NO deve scrivere accanto
		#    alla risposta la scena da cui l'ha data».  Questo file e' quella
		#    scena, e il giudice la stampa sopra ogni numero.
		SUONA="$SUONA" HZ="$HZ" USCITA="$USCITA" TONO_VIVO="$TONO_VIVO" \
		FINESTRA="$FINESTRA" python3 - "$LAV/$NOME.grafo.json" "$LAV/$NOME.stato.json" <<'FINE'
import json, os, sys
g = {}
try:
    g = json.load(open(sys.argv[1]))
except Exception as e:
    g = {"errore": f"grafo non leggibile: {e}"}
g.update({
    "scena_suona": os.environ["SUONA"] == "si",
    "tono_hz": int(os.environ["HZ"]),
    "tono_vivo_alla_fine": os.environ["TONO_VIVO"] == "true",
    "cliente_uscita": int(os.environ["USCITA"]),
    "finestra_s": int(os.environ["FINESTRA"]),
})
json.dump(g, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
FINE
		ok "giro «$NOME» finito · $(wc -l < "$LAV/$NOME.jsonl" 2>/dev/null || echo 0) blocchi nel JSONL"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	sblocca)
		# ⛔ IL BAN SI SBLOCCA, E SI DICHIARA — regola B0.3.  Questo banco
		#    autentica, quindi puo' bannare: senza lo sblocco dichiarato, «il
		#    ban non e' scattato» e «qualcuno l'ha tolto» hanno la stessa
		#    faccia.  ⚠ E il ban e' per INDIRIZZO: lasciarlo su metterebbe
		#    fuori uso tutti gli altri banchi per 12 ore.
		log "Lo sblocco dell'indirizzo — §4.4-bis"
		dentro "python3 $DENTRO_ALB/banchi/01-b8-sblocca.py --socket $DENTRO_LAV/comando.sock --ping"
		inf "ping al socket del comando: uscita $?"
		dentro "python3 $DENTRO_ALB/banchi/01-b8-sblocca.py --socket $DENTRO_LAV/comando.sock $IND"
		inf "sblocco di $IND: uscita $?"
		exit 0 ;;

	# ───────────────────────────────────────────────────────────────────
	spegni)
		# ⛔ SI SPEGNE LA MIA UNITA', PER NOME.  Non `pkill remotix`: sulla
		#    macchina ce ne sono altri, e stanno lavorando.
		log "Spengo $UNITA.service (e SOLO quella)"
		systemctl stop "$UNITA.service" 2>/dev/null
		systemctl reset-failed "$UNITA.service" 2>/dev/null
		rm -f "$LAV/parola"
		ok "spento · $(vicini)"
		exit 0 ;;

	*)
		log "Stato"
		inf "$(vicini)"
		inf "unita': $(systemctl is-active "$UNITA.service" 2>/dev/null)"
		inf "registro: $(stat -c %s "$LAV/registro.log" 2>/dev/null || echo 0) byte"
		exit 0 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE GIRA SUL PORTATILE — l'orchestratore
# ═══════════════════════════════════════════════════════════════════════════
SOLO_CANCELLO=0; RESTA_ACCESO=0; SOLO_SPEGNI=0
while [ $# -gt 0 ]; do
	case "$1" in
	--solo-cancello) SOLO_CANCELLO=1; shift ;;
	--resta-acceso)  RESTA_ACCESO=1; shift ;;
	--spegni)        SOLO_SPEGNI=1; shift ;;
	*) echo "⛔ argomento ignoto: $1" >&2; exit 2 ;;
	esac
done

QUI=$(cd "$(dirname "$0")/.." && pwd)
SUL_SERVER="bash $ALBERO/banchi/$(basename "$0") --sul-server"

# ⛔ `printf … | sudo -S` SI MANGIA LO STDIN, e in questo copione e' successo
#    due volte a chi l'ha scritto prima: la prima ha fatto leggere al `tar` la
#    parola d'ordine («gzip: stdin: not in gzip format»), la seconda ha dato a
#    `bash -s` uno stdin VUOTO — ⚠ e quella non ha dato nessun errore: il passo
#    stampava la sua intestazione e non faceva niente.  «Non ha fatto niente»
#    aveva la stessa faccia di «ha funzionato».
#    ⇒ Qui il copione **e' un file gia' sulla macchina** (ce lo porta il passo
#      1), e `sudo -S` riceve solo la parola.
# ⚠ E l'ORDINE conta: `env <variabili> <comando> <argomenti>`.  ⛔ Scritto
#   come `env $* …` il nome del passo finiva **prima** del comando, ed `env`
#   lo prendeva per il programma da eseguire: *«env: 'cancello': No such file
#   or directory»*, uscita 127.  Trovato girando, al primo giro vero.
remoto() # $1 = le variabili, $2 = il passo
{
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' env $1 $SUL_SERVER $2"
}

if [ "$SOLO_SPEGNI" = 1 ]; then
	remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA" spegni
	exit $?
fi

log "0 · Il terreno, dal portatile"
inf "banco 07-b43 · porta $PORTA · utente $UTENTE · albero $ALBERO"
inf "⛔ le porte $VICINE NON si toccano: sono di altri banchi"
ssh -o BatchMode=yes -o ConnectTimeout=10 "$MACCHINA" true || {
	ko "⛔ la macchina di prova non risponde"; exit 2; }
ok "$MACCHINA risponde"

log "1 · Porto i sorgenti in $ALBERO"
# ⛔ SENZA `sudo`: `printf … | sudo -S` mangerebbe lo stdin, che qui E' lo
#    stream del `tar`.  ⚠ E non serve: `/media/REMOTIX/src` e' di `nicfio`.
# ⛔ Si porta ANCHE `banchi/rcp`: il Makefile si rifiuta di compilare se non
#    puo' confrontare le due copie di `rcp.c` (R12.3) — e passare
#    `GEMELLO=nessuno` toglierebbe proprio il controllo che serve.
# ⛔ E si ESCLUDONO gli oggetti e il binario del portatile: spedendoli, `make`
#    troverebbe tutto aggiornato e non compilerebbe NIENTE, lasciando il
#    binario del portatile legato alla ngtcp2 di `/usr/local` — il difetto D5,
#    «un binario stantio resta verde».
# ⚠ E si porta SOLO quel che serve: `banchi/` intero fa 82 MB di registrazioni.
tar -C "$QUI" --exclude='*.o' --exclude='src/remotix' -czf - \
	src banchi/rcp \
	banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
	banchi/07-b42-giudice.py banchi/07-b43-giudizio.py \
	"banchi/$(basename "$0")" | \
	ssh -o BatchMode=yes "$MACCHINA" "mkdir -p $ALBERO && tar -C $ALBERO -xzf -" || {
	ko "⛔ i sorgenti non sono arrivati"; exit 2; }
ok "sorgenti in $ALBERO"

log "2 · Compilo dentro il contenitore"
# ⛔ Si chiama `costruisci.sh`, non `make`: e' lui che sa dove stanno ngtcp2 e
#    nghttp3 (in `/srv/src/b2`), cancella il binario PRIMA — cosi' «c'e'» vuol
#    dire «e' di adesso» — e controlla la marca dentro il binario prodotto.
# ⛔ E se la compilazione fallisce ci si FERMA, o il passo dopo accenderebbe il
#    BINARIO VECCHIO: misurerei il codice di prima credendo di misurare quello
#    nuovo.
if ! ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
	 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
	  bash $DENTRO_ALB/src/costruisci.sh 2>&1 | tail -20'"; then
	ko "⛔ la compilazione e' fallita: NON accendo niente"
	exit 2
fi
ok "compilato"

log "3 · ⛔ IL CANCELLO — «non c'e' ancora» non e' «non funziona»"
remoto "ALBERO=$ALBERO LAV=$LAV" cancello
CANCELLO=$?
if [ "$CANCELLO" = 4 ]; then
	printf '\n'
	printf '\033[1m⏳ IL PRODOTTO NON HA ANCORA LA CATTURA DELL AUDIO.\033[0m\n'
	printf '\n'
	printf '   Nel binario appena compilato non compaiono ne «support.null-audio-sink»\n'
	printf '   ne «monitor.channel-volumes», cioe le due stringhe che il sink della\n'
	printf '   sessione porta con se (`v1/remotix-c/src/suono.c`).  Il tono che il\n'
	printf '   server sa produrre oggi e `--audio-prova`, che lo fabbrica LUI: non e\n'
	printf '   il suono del desktop, ed e proprio quel che questo banco NON misura.\n'
	printf '\n'
	printf '   ⛔ Questo NON e un rosso: e un pezzo che non c e ancora\n'
	printf '      (`fasi/07-audio-e-appunti.md` §4.2 e §8).  Il banco e pronto e\n'
	printf '      aspetta; il giorno in cui `suono.c` entra nel prodotto, si rilancia\n'
	printf '      questo copione senza cambiargli una riga.\n'
	printf '\n'
	printf '   ⭐ E la meta che si puo gia credere: il GIUDICE e certificato (sei casi\n'
	printf '      su sei, `07-b40`), e il difetto del volume che non arriva al monitor\n'
	printf '      e stato RIPRODOTTO il 17 ago 2026 su due sink gemelli — la tabella\n'
	printf '      sta in cima a questo file.\n'
	printf '\n'
	exit 4
fi
[ "$CANCELLO" = 0 ] || { ko "⛔ il cancello si e' fermato (uscita $CANCELLO)"; exit 2; }
ok "il binario nomina il sink: si puo' misurare"
[ "$SOLO_CANCELLO" = 1 ] && exit 0

log "4 · Il terreno sulla macchina"
remoto "PORTA=$PORTA UTENTE=$UTENTE UID_B=$UID_B LAV=$LAV" terreno || {
	ko "⛔ il terreno non regge: non misuro"; exit 2; }

log "5 · Accendo il server e preparo la scena"
remoto "PORTA=$PORTA IND=$IND ALBERO=$ALBERO LAV=$LAV UNITA=$UNITA OPZIONI_SERVER='$OPZIONI_SERVER'" accendi || exit 2
spegni_tutto() {
	[ "$RESTA_ACCESO" = 1 ] && { inf "⚠ il server resta acceso sulla $PORTA (--resta-acceso)"; return; }
	remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA IND=$IND ALBERO=$ALBERO DENTRO_ALB=$DENTRO_ALB DENTRO_LAV=$DENTRO_LAV" sblocca
	remoto "PORTA=$PORTA LAV=$LAV UNITA=$UNITA" spegni
}
trap spegni_tutto EXIT

remoto "ALBERO=$ALBERO LAV=$LAV UTENTE=$UTENTE" parola || exit 2
remoto "LAV=$LAV AMPIEZZA=$AMPIEZZA HZ=$HZ_ATTESO SEC=$((SECONDI + 24))" tono || exit 2
remoto "LAV=$LAV AMPIEZZA=$AMPIEZZA HZ=$HZ_SBAGLIATO SEC=$((SECONDI + 24))" tono || exit 2

# ═══════════════════════════════════════════════════════════════════════════
# I GIRI — ⛔ e i due di mezzo sono DIFETTI INNESTATI: il banco e' verde solo
#          se glieli fa vedere.
# ═══════════════════════════════════════════════════════════════════════════
#
# | # | la scena                        | che cosa DEVE vedere il giudice        |
# |---|---------------------------------|----------------------------------------|
# | 1 | tono 440 Hz, volume pieno       | 440 Hz · rms **0,3536** · purezza ≥0,80 · VERDE |
# | 2 | ⛔ nessuno suona                | rms **< 0,01** con blocchi > 0 ⇒ ROSSO(SILENZIO) |
# | 3 | ⛔ suona a **660** Hz           | **660** Hz ⇒ ROSSO(FREQUENZA)          |
# | 4 | tono, volume al **25 %**        | rms = 0,3536 × **channelVolumes letto dal grafo** (≈ **0,0055**) ⇒ VERDE; se resta 0,3536 ⇒ ROSSO(VOLUME-NON-ARRIVA) |
# | 5 | tono, **muto**                  | rms **< 0,01** ⇒ VERDE; se arriva segnale ⇒ ROSSO(VOLUME-NON-ARRIVA) |
#
# ⛔ I giri 2 e 3 sono il controllo positivo **del banco**: la scena e' rotta
#    apposta, e il banco deve dirlo.  Se dicesse verde sarebbe cieco — ed e' la
#    forma di `LEZIONI.md` §2.2, la prova verde per tutto il tempo in cui il
#    difetto e' vivo.
# ⛔ I giri 4 e 5 sono il controllo positivo **del prodotto**: la scena e'
#    sana, e il rosso lo produrrebbe **il difetto di §kde §10.5** — il volume
#    che non arriva al monitor, che e' gia' costato una segnalazione
#    dell'utente.  ⭐ Il loro atteso non e' scritto a mano: si legge dal grafo.
# ⚠ L'ORDINE non e' libero, e va detto (`LEZIONI.md` §2.0-ter, «l'ordine e' una
#   variabile»): i giri 4 e 5 si appoggiano all'RMS del giro 1, quindi il 1
#   viene per primo per forza.  Fra il 2 e il 3 l'ordine e' indifferente, e la
#   scena di ciascuno viene **verificata** all'inizio del giro invece che
#   ereditata.

giro() # $1 nome  $2 suona  $3 hz  $4 volume  $5 rosso-atteso  $6 rms-da-giro
       # $7 descrizione  $8 atteso a parole
{
	# ⛔ NIENTE APOSTROFI nelle due frasi: viaggiano dentro `env VAR='…'`
	#    attraverso `ssh`, e un apostrofo chiude la stringa dalla parte
	#    sbagliata.  ⚠ Il sintomo sarebbe un comando remoto storto — cioe' un
	#    giro che non gira, con un messaggio che parla d'altro.  ⇒ Invece di
	#    ricordarselo, **lo si fa dire al banco**: e' la forma di `LEZIONI.md`
	#    §2.3-bis, «l'antidoto non e' ricordarsela».
	case "$7$8" in *"'"*)
		ko "⛔ difetto di BANCO: la descrizione del giro «$1» contiene un"
		ko "   apostrofo, e non sopravvive al viaggio dentro ssh.  Riscrivila."
		exit 2 ;;
	esac
	remoto "NOME='$1' SUONA=$2 HZ=$3 VOLUME=$4 ROSSO_ATTESO='$5' RMS_DA_GIRO='$6' \
DESCRIZIONE='$7' ATTESO_A_PAROLE='$8' \
PORTA=$PORTA IND=$IND UTENTE=$UTENTE UID_B=$UID_B SINK=$SINK ALBERO=$ALBERO LAV=$LAV \
DENTRO_ALB=$DENTRO_ALB DENTRO_LAV=$DENTRO_LAV SECONDI=$SECONDI FINESTRA=$FINESTRA \
MARGINE=$MARGINE RMS_BASE=$RMS_BASE HZ_ATTESO=$HZ_ATTESO" giro
}

log "6 · I giri"
giro "1-sano" si "$HZ_ATTESO" pieno "" "" \
	"un tono di $HZ_ATTESO Hz, ampiezza $AMPIEZZA, suonato da pw-play DENTRO la sessione, sink a volume pieno" \
	"$HZ_ATTESO Hz, rms $RMS_BASE, purezza >= 0,80 — VERDE"

giro "2-silenzio" no "$HZ_ATTESO" pieno SILENZIO "" \
	"la sessione NON suona niente: il sink esiste, il monitor consegna, nessuno ci scrive dentro" \
	"blocchi > 0 e rms < 0,01 ⇒ il banco DEVE dire ROSSO(SILENZIO), e distinguerlo da «non ho misurato»"

giro "3-frequenza" si "$HZ_SBAGLIATO" pieno FREQUENZA "" \
	"la sessione suona $HZ_SBAGLIATO Hz mentre il banco ne aspetta $HZ_ATTESO" \
	"$HZ_SBAGLIATO Hz ⇒ il banco DEVE dire ROSSO(FREQUENZA)"

giro "4-volume-25" si "$HZ_ATTESO" 0.25 "" "1-sano" \
	"stesso tono, ma il cursore del volume del sink al 25 % — §kde §10.5" \
	"rms = rms(1-sano) x channelVolumes letto dal grafo (~0,0055) ⇒ VERDE; se resta a $RMS_BASE ⇒ ROSSO(VOLUME-NON-ARRIVA)"

giro "5-muto" si "$HZ_ATTESO" muto "" "1-sano" \
	"stesso tono, ma il sink MUTO — la scena che ha aperto la misura di §kde §10.5" \
	"rms < 0,01 ⇒ VERDE; se arriva ancora segnale ⇒ ROSSO(VOLUME-NON-ARRIVA), e la cura si chiama «monitor.channel-volumes», in suono.c"

# ═══════════════════════════════════════════════════════════════════════════
log "7 · Il giudizio — ⭐ e lo strumento e' quello certificato di 07-b42"
# ⚠ Il giudizio gira **sul portatile**, non sulla macchina di prova: il
#   Goertzel a passo 1 Hz costa `[M]` ~4 s di CPU piena per ogni secondo
#   giudicato, e sulla macchina di prova ci sono altri banchi che misurano
#   tempi.  Un banco che scalda la CPU dei vicini falsa le loro misure
#   (`LEZIONI.md` §2.0-ter, la sorella delle finestre esclusive).
RACCOLTA=${RACCOLTA:-$QUI/banchi/07-b43-copie}
mkdir -p "$RACCOLTA"
rm -f "$RACCOLTA"/*.jsonl "$RACCOLTA"/*.json
ssh -o BatchMode=yes "$MACCHINA" \
	"tar -C $LAV -cf - --ignore-failed-read \$(cd $LAV && ls *.jsonl *.atteso.json *.stato.json 2>/dev/null)" \
	| tar -C "$RACCOLTA" -xf - || { ko "⛔ non ho riportato i file da giudicare"; exit 2; }
inf "riportati in $RACCOLTA: $(ls "$RACCOLTA" | tr '\n' ' ')"

python3 "$QUI/banchi/07-b43-giudizio.py" "$RACCOLTA"
G=$?
case "$G" in
0) ok "⭐ VERDE: ogni giro ha fatto quel che era dichiarato prima" ;;
1) ko "⛔ IL PRODOTTO E' ROSSO — il motivo e la regola stanno qui sopra" ;;
2) ko "⚠ NON HO MISURATO — e non e' un rosso del prodotto (CODER.md §3.10)" ;;
3) ko "⛔⛔ IL BANCO E' CIECO: un difetto innestato non e' stato visto." ;;
esac
exit "$G"
