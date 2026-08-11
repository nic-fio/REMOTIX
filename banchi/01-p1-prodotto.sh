#!/bin/bash
#
# 01-p1-prodotto.sh — gira SUL SERVER.  P1: il PRODOTTO si accende.
#
#   bash /media/REMOTIX/src/01-p1-prodotto.sh              il giro intero
#   bash /media/REMOTIX/src/01-p1-prodotto.sh previsione   che cosa mi aspetto
#
# E poi, da CHUWI, il registro si riporta nell'albero — ⛔ e questa riga fa
# parte del banco, non e' un contorno: il registro che resta sul server e' il
# registro che sparisce alla prossima risincronizzazione (`banchi/prodotto/LEGGIMI.md`):
#
#   scp nicfio@192.168.0.2:/media/REMOTIX/src/01-p1-esiti.jsonl banchi/01-p1-esiti.jsonl
#
# -----------------------------------------------------------------------------
# ⛔ CHE COSA MISURA, E PERCHE' ESISTE
#
# Fino all'11 agosto 2026 `src/costruisci.sh` non era mai stato eseguito da
# nessuna parte in questo albero, e nessuno dei 14 script di lancio accendeva il
# prodotto: `bsslserver` — l'INNESTO, un altro server — compariva in 11 di loro,
# il binario `remotix` in **zero**.  Sul server c'era un `remotix` del 10 agosto
# 21:08, cioe' **di prima** delle cure della notte.
#
# ⭐ Questo banco rifa' da capo, in un giro solo:
#
#   1. costruzione dai sorgenti di adesso, dentro il contenitore;
#   2. ⛔ la prova che il binario e' QUELLO NUOVO — non «c'e' un binario»;
#   3. accensione, prova di fumo, spegnimento;
#   4. ⛔ i controlli positivi dello strumento, che devono uscire ROSSI.
#
# -----------------------------------------------------------------------------
# ⛔⭐ COME SI DIMOSTRA CHE IL BINARIO E' NUOVO — e come apparirebbe il contrario
#
# `LEZIONI.md` §1.11: una prova indiretta prova quel che prova.  Qui le prove
# sono **tre**, e nessuna da sola basterebbe:
#
#   | prova                    | il caso contrario avrebbe questo aspetto        |
#   |--------------------------|-------------------------------------------------|
#   | il costruttore e' uscito | uno stato diverso da zero — e allora il binario  |
#   | 0                        | sul disco, se c'e', non e' di adesso             |
#   | la data del file sta     | data anteriore all'inizio del giro: il binario   |
#   | dentro il giro           | e' rimasto quello di ieri                        |
#   | ⭐ le tre marche nuove    | ⛔ `NON-BANNATO`, `PING del trasporto` e         |
#   |                          | `/etc/pam.d/remotix` ASSENTI: e' il binario di   |
#   |                          | prima delle cure della notte del 10 agosto       |
#   | ⭐ l'impronta NON e' la   | `2b029201…`, 385848 byte: e' esattamente il      |
#   | `2b029201…` del 10 ago   | binario stantio, nominato per esteso             |
#
# ⚠ E una prova che qui NON c'e', ed e' stata tolta dopo averla misurata:
#   *«l'impronta e' cambiata rispetto a prima»*.  ⛔ La costruzione e'
#   riproducibile — due giri a sorgenti immutati danno lo stesso sha256 — e
#   quella riga chiamava rosso il comportamento migliore di un costruttore.
#
# ⛔ E la terza vale solo insieme al suo controllo positivo: se il cercatore di
#    marche non trovasse nemmeno `GCC:` — che in un binario compilato c'e' di
#    sicuro — i suoi «non c'e'» non varrebbero niente (`LEZIONI.md` §1.9
#    regola 2, e la prima stesura di `costruisci.sh` ci e' inciampata davvero,
#    dichiarando assenti cinque marche perche' mancava `strings`).
#
# -----------------------------------------------------------------------------
# ⛔ LE DUE PORTE DEL CONTENITORE, E SI DICHIARA QUALE SI E' USATA
#
# La porta di casa e' `enter.sh`, che chiede la password di sudo.  ⚠ Una
# sessione senza terminale — un agente via `ssh -o BatchMode=yes`, un cron —
# non ha nessuno che la digiti, e `enter.sh` esce con «a password is required».
#
# ⭐ Il ripiego e' `unshare -Ur chroot`, che entra nello STESSO `devroot` con lo
#    stesso compilatore e le stesse librerie, ma da utente normale: dentro si e'
#    root, fuori si resta `nicfio`.  ⛔ Non e' la stessa cosa, e le differenze
#    si dichiarano invece di tacerle (`CODER.md` §4.2 — un ripiego silenzioso
#    produce due comportamenti sotto la stessa etichetta):
#
#      · i file prodotti appartengono a `nicfio`, non a `root`;
#      · non si puo' scrivere in `/etc` del contenitore — quindi
#        `costruisci.sh` non installerebbe `/etc/pam.d/remotix` se mancasse
#        (l'11 agosto 2026 c'era gia', e lo dice da se');
#      · non si possono aprire porte sotto la 1024 — e la 7448 non lo e'.
#
# ⛔ La porta usata finisce in OGNI riga del registro, campo `porta_contenitore`.
#
# -----------------------------------------------------------------------------
# ⛔⭐ LA PORTA E IL SORGENTE SI POSSONO CAMBIARE — e la modifica e' DICHIARATA
#     qui, sera dell'11 agosto 2026, per la certificazione di P1 sotto B12.
#
# Prima di stasera `PORTA=7448` e `SORG=$FUORI/remotix` erano scritti dentro:
# questo banco poteva girare solo contro l'unico prodotto della macchina, e
# ⛔ **costruire vuol dire riscrivere `/media/REMOTIX/src/remotix/remotix`** —
# cioe' il binario del server che gli altri banchi stanno usando.  Per
# certificare P1 servono TRE giri (sano → guasto → sano), e il giro col guasto
# lascerebbe per qualche minuto un binario bugiardo sotto i piedi di chiunque
# altro riaccendesse il prodotto.  ⭐ Da cui due variabili d'ambiente:
#
#   PORTA        la porta su cui accendere      (def. 7448)
#   SORG         la cartella dei sorgenti       (def. $FUORI/remotix)
#   DENTRO_SORG  la stessa, vista dal contenitore (dedotta da SORG)
#   PREFISSO_TMP il prefisso dei file di lavoro (def. p1)
#
# ⛔ E il valore predefinito NON e' cambiato: chi lancia questo banco a mano
#    misura esattamente quel che misurava prima.  ⚠ La certificazione di B12 lo
#    lancia invece su una **copia intera** del prodotto, con la sua porta:
#
#      cp -a /media/REMOTIX/src/remotix /media/REMOTIX/src/01-b12-copie/p1-remotix
#      PORTA=7501 PORTA_MORTA=7502 PREFISSO_TMP=sera-p15 \
#        SORG=/media/REMOTIX/src/01-b12-copie/p1-remotix \
#        bash /media/REMOTIX/src/01-p1-prodotto.sh
#
#    ⛔ La copia si rifa' PRIMA di ogni giro sano, e per la ragione che
#    `01-b12-guasti.py` scrive su `prepara_copia()`: una copia rimasta da un
#    giro precedente potrebbe portarsi dietro il guasto di quel giro, e il
#    banco partirebbe **gia' rosso** — cioe' il verde di partenza, che e' meta'
#    della certificazione, sarebbe perso senza che nessuno lo veda.
#
# -----------------------------------------------------------------------------
# ⛔ I CONFINI (mandato dell'11 agosto 2026)
#
#   · ⛔ **porta 7448**.  La 7447 e' `bsslserver`, l'innesto: non si tocca, e
#     questo banco non la nomina nemmeno per guardarla;
#   · ⛔ **nessuna autenticazione, quindi nessun ban**: §4.4-bis mette fuori un
#     indirizzo per 12 ore dopo tre parole d'ordine sbagliate, e mezza giornata
#     di macchina vale piu' di una riga di banco.  ⭐ Questo banco **non chiama
#     mai lo sblocco**, e lo dichiara qui: cosi' «il ban non e' scattato» e
#     «qualcuno l'ha tolto» non hanno lo stesso aspetto (regola B0.3);
#   · il file dei ban e' **suo**, `/srv/src/tmp/p1-ban`, e nessun altro banco lo
#     nomina.
#
# -----------------------------------------------------------------------------
# ⛔ NIENTE REDIREZIONI ATTORNO A `enter.sh` — la regola pagata quattro volte il
#    10 agosto 2026.  Si redirige DENTRO le virgolette e si legge il file dopo.
# -----------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
DEVROOT=/media/REMOTIX/devroot
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
# ⛔ SORG e' il percorso VISTO DA FUORI; DENTRO_SORG lo stesso visto dal
#    contenitore.  ⚠ Si ricava per sottrazione del prefisso, non si indovina:
#    due verita' sullo stesso percorso e' la forma con cui i guasti si perdono
#    per strada (la stessa nota che `01-b12-guasti.py` scrive su `{CERT}`).
SORG=${SORG:-$FUORI/remotix}     # == /srv/src/remotix dentro il contenitore
DENTRO_SORG=${DENTRO_SORG:-$DENTRO/${SORG#"$FUORI/"}}
TMP=$FUORI/tmp
ESITI=$FUORI/01-p1-esiti.jsonl
PORTA=${PORTA:-7448}
PORTA_MORTA=${PORTA_MORTA:-7449}
PREFISSO_TMP=${PREFISSO_TMP:-p1}

FUSO="$(date +%:z) $(date +%Z) — ⚠ l'orologio del server e' ~2 h indietro rispetto a CHUWI (CEST)"
INIZIO_EPOCA=$(date +%s)
GIRO=$(date +%Y%m%dT%H%M%S%z)

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# --- il registro -------------------------------------------------------------
jesc() { local s=${1-}; s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n};
         s=${s//$'\t'/\\t}; s=${s//$'\r'/}; printf '%s' "$s"; }

CONT=?                            # quale porta del contenitore si e' usata
PROVATI=0; PASSATI=0
riga() # $1 passo, $2 esito 1/0/-, $3 dettaglio, $4 (facolt.) coppie JSON in piu'
{
	printf '{"banco":"01-p1","giro":"%s","quando":"%s","fuso":"%s","macchina":"%s","porta_contenitore":"%s","passo":"%s","esito":"%s","dettaglio":"%s"%s}\n' \
	  "$GIRO" "$(date -Is)" "$(jesc "$FUSO")" "$(hostname)" "$CONT" \
	  "$(jesc "$1")" "$2" "$(jesc "${3-}")" "${4:+,$4}" >> "$ESITI"
	case "$2" in
		1) PROVATI=$((PROVATI+1)); PASSATI=$((PASSATI+1)); ok "$1 — ${3-}" ;;
		0) PROVATI=$((PROVATI+1));                         ko "$1 — ${3-}" ;;
		*)                                                 inf "$1 — ${3-}" ;;
	esac
}

# --- la porta del contenitore ------------------------------------------------
scegli_porta()
{
	# ⚠ Si interroga `sudo`, non `enter.sh`: chiederlo a `enter.sh` vorrebbe
	#   dire lanciarlo, e senza terminale resterebbe fermo su una domanda che
	#   nessuno vede.
	if sudo -n true 2>/dev/null; then
		CONT=enter.sh
	elif [ -t 0 ]; then
		CONT=enter.sh
	else
		CONT=userns
	fi
	if [ "$CONT" = enter.sh ]; then
		# ⛔ Nessuna redirezione qui attorno: e' la riga che si prende la
		#    richiesta di password, e da qui in poi sudo e' valido.
		bash "$ENTRA" --root "true" || { CONT=userns; }
	fi
	if [ "$CONT" = userns ]; then
		unshare -Ur /usr/sbin/chroot "$DEVROOT" /bin/true 2>/dev/null || {
			ko "⛔ nessuna delle due porte del contenitore si apre"
			riga contenitore.aperto 0 "ne' enter.sh (serve la password di sudo) ne' unshare -Ur chroot"
			exit 2
		}
	fi
}

dentro() # $1 = comando da eseguire dentro il contenitore
{
	if [ "$CONT" = enter.sh ]; then
		bash "$ENTRA" --root "$1"
	else
		unshare -Ur /usr/sbin/chroot "$DEVROOT" /usr/bin/env -i \
		  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
		  HOME=/root USER=root LC_ALL=C.UTF-8 /bin/bash -c "$1"
	fi
}

# --- gli strumenti di misura, fuori dal contenitore --------------------------
# ⛔ `sha256sum` sull'elenco ORDINATO, e il conto dei file si stampa accanto:
#    un'impronta senza il suo denominatore non dice su che cosa ha guardato
#    (`LEZIONI.md` §1.9 regola 4).
#
# ⛔⭐ E NON SI CHIAMA CON UNA SOSTITUZIONE DI COMANDO — difetto misurato sul
#    primo giro di questo banco, alle 04:52 del'11 agosto 2026.  La prima
#    stesura faceva `IMP_SORG=$(impronta_sorgenti)`: la sostituzione apre una
#    SOTTOSHELL, e il conteggio dei file assegnato li' dentro moriva con lei.
#    ⛔ Il registro ha scritto un'impronta perfetta accanto a **«0 file»**, cioe'
#    la quinta regola di §1.9 in persona: *un denominatore falso e' peggio di
#    nessun denominatore, perche' da' alla misura l'aria di essere gia' stata
#    controllata*.  Adesso i due valori escono per riferimento, insieme.
FILE_SORGENTE=0
IMP_SORG=""
impronta_sorgenti()
{
	local elenco
	elenco=$(cd "$SORG" && ls -1 *.c *.h Makefile costruisci.sh pagina.html remotix.pam 2>/dev/null | sort)
	FILE_SORGENTE=$(printf '%s\n' "$elenco" | grep -c .)
	IMP_SORG=$( (cd "$SORG" && printf '%s\n' "$elenco" | xargs sha256sum) | sha256sum | cut -d' ' -f1 )
}

MARCHE=("REMOTIX_V2 — fase 1" "Cross-Origin-Embedder-Policy" \
        "Cross-Origin-Opener-Policy" "/rcp/1" "/impronta" \
        "NON-BANNATO" "PING del trasporto" "/etc/pam.d/remotix")
# ⭐ Le ultime tre sono le cure della notte del 10 agosto: il binario delle
#    21:08 NON le aveva, ed e' questo che rende la prova capace di DISTINGUERE.
MARCHE_NUOVE=("NON-BANNATO" "PING del trasporto" "/etc/pam.d/remotix")

conta_marche() # $1 = file.  Stampa «presenti/totali» e l'elenco delle mancanti
{
	local f=$1 m pres=0 manca=""
	if [ ! -e "$f" ]; then printf '0/%s — il file non esiste\n' "${#MARCHE[@]}"; return; fi
	for m in "${MARCHE[@]}"; do
		if grep -a -F -q -e "$m" -- "$f"; then pres=$((pres+1)); else manca="$manca «$m»"; fi
	done
	printf '%s/%s%s\n' "$pres" "${#MARCHE[@]}" "${manca:+ — mancano:$manca}"
}

# =============================================================================
if [ "${1:-}" = previsione ]; then
	cat <<'FINE'

== P1, la previsione — che cosa mi aspetto, PRIMA di misurare

  1. `costruisci.sh` esce 0, e prima di compilare ha cancellato il binario
     vecchio.  ⚠ L'impronta dopo puo' essere IDENTICA a quella prima, e non e'
     un difetto: la costruzione e' riproducibile.  Quel che non puo' essere e'
     `2b029201…`, l'impronta del binario del 10 agosto 21:08.
  2. Il binario nuovo porta tutte e otto le marche.  Il binario del 10 agosto
     21:08 ne portava CINQUE: gli mancavano `NON-BANNATO`, `PING del
     trasporto` e `/etc/pam.d/remotix`.  ⛔ Se dopo la costruzione ne mancasse
     anche una sola, la costruzione non ha sostituito niente.
  3. Il server si accende sulla 7448, serve la pagina con le tre intestazioni
     di isolamento e l'impronta del certificato di sessione dentro il corpo,
     risponde 404 su un percorso inesistente, ascolta in UDP e in TCP sullo
     stesso numero, e risponde PONG sul socket di comando.
  4. TERM basta a spegnerlo.
  5. ⛔ I quattro controlli positivi escono ROSSI: la costruzione guasta
     fallisce E lascia il disco senza binario; la sonda puntata su una porta
     vuota non dice «0 200»; il cercatore di marche non trova una marca
     inventata; ⭐ e il controllo «e' quello nuovo», puntato sul binario del 10
     agosto tenuto in riserva, trova ZERO delle tre marche della notte.

  ⚠ Quel che questo banco NON prova, e va letto qui invece che dedotto: la
    stretta di mano RCP, l'autenticazione, il ban di §4.4-bis, lo sblocco.
    Sono di B7, B8 e B10, e provarli qui costerebbe l'indirizzo per 12 ore.
FINE
	exit 0
fi

# =============================================================================
log "P1 — il prodotto si accende.  Giro $GIRO"
inf "fuso: $FUSO"
inf "porta del prodotto: $PORTA   ⛔ la 7447 (bsslserver) non si tocca"
# ⛔ B0.1: lo stato iniziale si DICHIARA.  Da stasera la sorgente e la porta si
#    possono cambiare, e quale delle due si e' usata non si deduce dal contesto.
inf "sorgente:  $SORG   (dentro il contenitore: $DENTRO_SORG)"
inf "porta morta (controllo C2): $PORTA_MORTA   ·   prefisso dei file: $PREFISSO_TMP"
if [ "$SORG" != "$FUORI/remotix" ]; then
	inf "⚠ NON e' il prodotto di casa: e' una COPIA.  Il prodotto in $FUORI/remotix"
	inf "  non viene ne' ricostruito ne' toccato da questo giro."
fi

log "La porta del contenitore"
scegli_porta
riga contenitore.aperto 1 "sono entrato dal contenitore per la porta «$CONT»"

log "L'impronta dei sorgenti, PRIMA di toccare qualunque cosa"
impronta_sorgenti
riga sorgenti.impronta "$([ "$FILE_SORGENTE" -gt 0 ] && echo 1 || echo 0)" \
  "sha256 delle impronte ordinate di $FILE_SORGENTE file di $SORG = $IMP_SORG   ⛔ con ZERO file questa impronta non direbbe niente su niente" \
  "\"impronta_sorgenti\":\"$IMP_SORG\",\"file_sorgente\":$FILE_SORGENTE"

log "Il binario PRIMA di costruire"
if [ -e "$SORG/remotix" ]; then
	IMP_PRIMA=$(sha256sum "$SORG/remotix" | cut -d' ' -f1)
	DATA_PRIMA=$(stat -c '%y' "$SORG/remotix")
	MAR_PRIMA=$(conta_marche "$SORG/remotix")
else
	IMP_PRIMA="(nessun binario)"; DATA_PRIMA="-"; MAR_PRIMA="-"
fi
riga binario.prima - "impronta $IMP_PRIMA · data $DATA_PRIMA · marche $MAR_PRIMA" \
  "\"impronta_prima\":\"$(jesc "$IMP_PRIMA")\",\"marche_prima\":\"$(jesc "$MAR_PRIMA")\""

log "La costruzione, dentro il contenitore"
# ⛔ La marca dello stato va APPESA ALLO STESSO FILE, non stampata a terminale:
#    la prima stesura scriveva `… > log 2>&1; printf 'P1-COSTRUISCI=%s' $?`, e
#    quel `printf` finiva sullo schermo mentre il `grep` cercava nel file.  Il
#    banco ha dichiarato «nessuno stato letto» su una costruzione riuscita —
#    un rosso puntato sull'imputato sbagliato (`LEZIONI.md` §1.9, settima
#    veste), misurato alle 04:52 dell'11 agosto 2026.
dentro "bash $DENTRO_SORG/costruisci.sh > $DENTRO/tmp-$PREFISSO_TMP-costruisci.log 2>&1; printf 'P1-COSTRUISCI=%s\n' \$? >> $DENTRO/tmp-$PREFISSO_TMP-costruisci.log"
COSTR=$(grep -a -o 'P1-COSTRUISCI=[0-9]*' "$FUORI/tmp-$PREFISSO_TMP-costruisci.log" 2>/dev/null | tail -1 | cut -d= -f2)
# ⚠ La riga finale la stampa il comando DENTRO le virgolette, e non si legge
#   dallo stato d'uscita di `enter.sh`: che quello lo propaghi non l'ha mai
#   verificato nessuno (rilievo R5.21, ancora aperto).  ⛔ E se la riga NON
#   arriva non si ricostruisce «per sicurezza»: si dichiara che lo stato non si
#   e' letto, che non e' la stessa cosa di «e' andata male».
tail -n 25 "$FUORI/tmp-$PREFISSO_TMP-costruisci.log" 2>/dev/null
riga costruzione.esito "$([ "${COSTR:-9}" = 0 ] && echo 1 || echo 0)" \
  "costruisci.sh e' uscito «${COSTR:-nessuno stato letto}» (atteso 0)" \
  "\"stato_costruttore\":\"$(jesc "${COSTR:-}")\""

log "Il binario DOPO, e la domanda vera: e' QUELLO NUOVO?"
if [ ! -e "$SORG/remotix" ]; then
	riga binario.presente 0 "⛔ dopo la costruzione il binario non c'e'"
	IMP_DOPO="(nessuno)"; DATA_DOPO="-"; EPOCA_DOPO=0; MAR_DOPO="-"
else
	IMP_DOPO=$(sha256sum "$SORG/remotix" | cut -d' ' -f1)
	DATA_DOPO=$(stat -c '%y' "$SORG/remotix")
	EPOCA_DOPO=$(stat -c '%Y' "$SORG/remotix")
	MAR_DOPO=$(conta_marche "$SORG/remotix")
	riga binario.presente 1 "impronta $IMP_DOPO · data $DATA_DOPO"
fi
# ⛔⭐ «L'IMPRONTA E' CAMBIATA» NON E' UN CRITERIO, ED E' STATO IL PRIMO ROSSO
#     FALSO DI QUESTO BANCO (giro delle 04:52 dell'11 agosto 2026).
#
# La costruzione e' RIPRODUCIBILE: due giri a sorgenti immutati, alle 04:45 e
# alle 04:52, hanno prodotto lo **stesso** sha256 — `7b871ef8…`.  Un banco che
# pretenda l'impronta diversa chiama rosso il comportamento migliore che un
# costruttore possa avere.  ⭐ E il rovescio e' che l'impronta diventa una
# funzione dei sorgenti: vale come **attestazione**, non come cambiamento.
#
# ⛔ Quindi qui si registra il fatto (esito «-», due letture dichiarate) e il
#    criterio si sposta sulle tre prove che DISTINGUONO: la data, le marche, e
#    l'impronta del binario stantio, che si nomina per esteso qui sotto.
if [ "$IMP_DOPO" = "$IMP_PRIMA" ]; then
	LETTURA="identica a prima — costruzione riproducibile a sorgenti immutati, NON «non ha ricostruito»: lo stato del costruttore e la data lo dicono"
else
	LETTURA="diversa da prima — sorgenti o ambiente cambiati fra i due giri"
fi
riga binario.impronta - "prima $IMP_PRIMA · dopo $IMP_DOPO — $LETTURA" \
  "\"impronta_binario\":\"$(jesc "$IMP_DOPO")\",\"impronta_binario_prima\":\"$(jesc "$IMP_PRIMA")\""

# ⭐ La prova che esclude il binario stantio per NOME, e non per differenza:
#    quello del 10 agosto 21:08 UTC e' `2b029201…`, 385848 byte.  ⛔ Il caso
#    contrario ha un aspetto preciso: questa riga rossa, e le tre marche della
#    notte assenti qui sotto.
STANTIO=2b029201a114fb779589d0fca3abbef3311f561027e32eefb32c6e8e2a713b95
riga binario.non.e.quello.del.10ago "$([ "$IMP_DOPO" != "$STANTIO" ] && echo 1 || echo 0)" \
  "l'impronta non e' quella del binario delle 21:08 del 10 agosto ($STANTIO)"
riga binario.data.dentro.il.giro "$([ "${EPOCA_DOPO:-0}" -ge "$INIZIO_EPOCA" ] && echo 1 || echo 0)" \
  "il file e' stato scritto dopo l'inizio del giro ($(date -Is -d @$INIZIO_EPOCA))"
riga binario.marche "$([ "${MAR_DOPO%%/*}" = "${#MARCHE[@]}" ] && echo 1 || echo 0)" \
  "marche trovate: $MAR_DOPO   (prima erano: $MAR_PRIMA)" \
  "\"marche_dopo\":\"$(jesc "$MAR_DOPO")\",\"marche_cercate\":${#MARCHE[@]}"

# ⭐ La prova che DISTINGUE, e il caso contrario e' scritto accanto.
NUOVE=0
for m in "${MARCHE_NUOVE[@]}"; do
	grep -a -F -q -e "$m" -- "$SORG/remotix" 2>/dev/null && NUOVE=$((NUOVE+1))
done
riga binario.e.quello.nuovo "$([ "$NUOVE" = "${#MARCHE_NUOVE[@]}" ] && echo 1 || echo 0)" \
  "$NUOVE/${#MARCHE_NUOVE[@]} marche della notte del 10 agosto.  ⛔ Il caso contrario: il binario delle 21:08 ne aveva ZERO — impronta 2b029201…, 385848 byte" \
  "\"marche_nuove_trovate\":$NUOVE,\"marche_nuove_cercate\":${#MARCHE_NUOVE[@]}"

log "Il giro acceso e spento, e la prova di fumo"
# ⛔ L'altra meta' del banco dev'essere accanto a questa, in $FUORI: e' l'unica
#    cartella che il contenitore vede (== /srv/src).  Se manca si dice, invece
#    di raccogliere zero fatti e chiamarli verdi.
if [ ! -f "$FUORI/01-p1-dentro.sh" ]; then
	riga fumo.attrezzo 0 "⛔ manca $FUORI/01-p1-dentro.sh: copiare tutt'e due i file di 01-p1- sul server"
fi
# ⛔ Le variabili si passano DENTRO le virgolette, davanti a `bash`: sono
#    l'unica strada che attraversa tutt'e due le porte del contenitore
#    (`enter.sh --root "…"` e `unshare -Ur chroot … env -i bash -c "…"`), e
#    `env -i` cancella tutto quel che si esportasse qui fuori.
AMB="D=$DENTRO_SORG PORTA=$PORTA PORTA_MORTA=$PORTA_MORTA PREFISSO_TMP=$PREFISSO_TMP"
dentro "$AMB bash $DENTRO/01-p1-dentro.sh fumo > $DENTRO/tmp-$PREFISSO_TMP-fumo.log 2>&1; printf 'P1-FUMO=%s\n' \$? >> $DENTRO/tmp-$PREFISSO_TMP-fumo.log"
sed -n '1,400p' "$FUORI/tmp-$PREFISSO_TMP-fumo.log" 2>/dev/null
FUMO_PROVATI=0; FUMO_PASSATI=0
while read -r _ nome esito dett; do
	riga "fumo.$nome" "$esito" "$dett"
	FUMO_PROVATI=$((FUMO_PROVATI+1))
	[ "$esito" = 1 ] && FUMO_PASSATI=$((FUMO_PASSATI+1))
done < <(grep -a '^FATTO ' "$FUORI/tmp-$PREFISSO_TMP-fumo.log" 2>/dev/null)
if [ "$FUMO_PROVATI" -eq 0 ]; then
	riga fumo.denominatore 0 "⛔ ZERO fatti raccolti: la fase di fumo non ha misurato NIENTE — un verdetto su zero cose supera qualunque criterio (LEZIONI.md §1.9 regola 6)"
fi

log "I controlli positivi: lo strumento sa diventare rosso?"
dentro "$AMB bash $DENTRO/01-p1-dentro.sh controlli > $DENTRO/tmp-$PREFISSO_TMP-controlli.log 2>&1; printf 'P1-CTRL=%s\n' \$? >> $DENTRO/tmp-$PREFISSO_TMP-controlli.log"
sed -n '1,200p' "$FUORI/tmp-$PREFISSO_TMP-controlli.log" 2>/dev/null
CTRL_PROVATI=0; CTRL_PASSATI=0
while read -r _ nome esito dett; do
	riga "controllo.$nome" "$esito" "$dett"
	CTRL_PROVATI=$((CTRL_PROVATI+1))
	[ "$esito" = 1 ] && CTRL_PASSATI=$((CTRL_PASSATI+1))
done < <(grep -a '^FATTO ' "$FUORI/tmp-$PREFISSO_TMP-controlli.log" 2>/dev/null)
if [ "$CTRL_PROVATI" -eq 0 ]; then
	riga controllo.denominatore 0 "⛔ ZERO controlli positivi eseguiti: questo banco non ha mostrato di saper vedere un fallimento"
fi

# -----------------------------------------------------------------------------
# ⛔⭐ C4 — IL CONTROLLO CHE VALE PIU' DEGLI ALTRI TRE: lo stesso identico
#     controllo di sopra, puntato sul BINARIO STANTIO.
#
# «Le tre marche ci sono» e' una prova solo se si sa che cosa sarebbe successo
# col binario sbagliato (`LEZIONI.md` §1.11 regola 1).  Qui il binario sbagliato
# esiste davvero — `2b029201…`, 385848 byte, 10 agosto 21:08 UTC — ed e' stato
# salvato in `/media/REMOTIX/tmp/riserva-11ago/prima-della-sincronia.tgz` prima
# che `costruisci.sh` lo cancellasse.  ⛔ Su di lui questo controllo DEVE uscire
# rosso; se uscisse verde, i verdi di sopra non varrebbero niente.
log "C4 — lo stesso controllo, puntato sul binario STANTIO del 10 agosto"
STANTIO_FILE=$TMP/$PREFISSO_TMP-stantio/remotix/remotix
RISERVA=/media/REMOTIX/tmp/riserva-11ago/prima-della-sincronia.tgz
if [ ! -e "$STANTIO_FILE" ] && [ -f "$RISERVA" ]; then
	mkdir -p "$TMP/$PREFISSO_TMP-stantio"
	tar xzf "$RISERVA" -C "$TMP/$PREFISSO_TMP-stantio" remotix/remotix 2>/dev/null
fi
if [ ! -e "$STANTIO_FILE" ]; then
	# ⛔ «non ho potuto guardare» non e' «e' andato bene»: e' rosso, e dice perche'.
	riga controllo.c4.stantio.rosso 0 \
	  "⛔ NON ho potuto guardare: manca $STANTIO_FILE e non l'ho estratto da $RISERVA"
	CTRL_PROVATI=$((CTRL_PROVATI+1))
else
	NS=0
	for m in "${MARCHE_NUOVE[@]}"; do
		grep -a -F -q -e "$m" -- "$STANTIO_FILE" 2>/dev/null && NS=$((NS+1))
	done
	IMP_ST=$(sha256sum "$STANTIO_FILE" | cut -d' ' -f1)
	riga controllo.c4.stantio.rosso "$([ "$NS" -eq 0 ] && echo 1 || echo 0)" \
	  "sul binario stantio ($IMP_ST) le marche della notte sono $NS/${#MARCHE_NUOVE[@]} — atteso 0, e marche in tutto: $(conta_marche "$STANTIO_FILE")" \
	  "\"marche_nuove_sullo_stantio\":$NS"
	CTRL_PROVATI=$((CTRL_PROVATI+1))
	[ "$NS" -eq 0 ] && CTRL_PASSATI=$((CTRL_PASSATI+1))
fi

# -----------------------------------------------------------------------------
log "Nessun processo resta acceso"
RESTA=$(pgrep -f "remotix .*--porta $PORTA" | tr '\n' ' ')
riga nessuno.resta.acceso "$([ -z "$RESTA" ] && echo 1 || echo 0)" \
  "processi «remotix … --porta $PORTA» ancora vivi: ${RESTA:-nessuno}"

# -----------------------------------------------------------------------------
# ⛔ IL VERDETTO PORTA IL SUO DENOMINATORE, e se il denominatore e' zero non
#    esiste nessun verdetto: «tutti quelli provati sono andati bene» e' vero
#    anche quando i provati sono zero (`LEZIONI.md` §1.9 regola 6).
log "Il verdetto, col denominatore accanto"
DEN="\"passi_provati\":$PROVATI,\"passi_passati\":$PASSATI,\"fumo_provati\":$FUMO_PROVATI,\"fumo_passati\":$FUMO_PASSATI,\"controlli_provati\":$CTRL_PROVATI,\"controlli_passati\":$CTRL_PASSATI,\"file_sorgente\":$FILE_SORGENTE,\"marche_cercate\":${#MARCHE[@]}"
if [ "$PROVATI" -eq 0 ] || [ "$FUMO_PROVATI" -eq 0 ] || [ "$CTRL_PROVATI" -eq 0 ]; then
	VERDETTO="NESSUNO — un denominatore e' zero"
	E=0
elif [ "$PASSATI" -eq "$PROVATI" ]; then
	VERDETTO="VERDE"; E=1
else
	VERDETTO="ROSSO"; E=0
fi
riga verdetto "$E" "$VERDETTO — $PASSATI su $PROVATI controlli, di cui fumo $FUMO_PASSATI/$FUMO_PROVATI e controlli positivi $CTRL_PASSATI/$CTRL_PROVATI" "$DEN"

printf '\n'
inf "registro: $ESITI  (da riportare nell'albero con scp, vedi la testa di questo file)"
[ "$E" = 1 ] || exit 1
