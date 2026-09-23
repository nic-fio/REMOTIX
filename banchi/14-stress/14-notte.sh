#!/bin/bash
# ===========================================================================
# 14-notte.sh — ⭐⭐ LA REGIA DELLA NOTTE: chi gira, in che ordine, e con che tetto
# ===========================================================================
#
#   bash 14-notte.sh elenco                  dice che cosa farebbe, in ordine
#   bash 14-notte.sh gira                    la matrice intera
#   bash 14-notte.sh gira --secco            a vuoto: la regia si prova da sola
#   bash 14-notte.sh gira --scatola "gnome"  solo quelle scatole
#   bash 14-notte.sh gira --marca firefox    solo quel browser
#   bash 14-notte.sh gira --scenario pesante solo quello scenario
#   bash 14-notte.sh gira --da-capo          rifa' anche i giri gia' giudicati
#   bash 14-notte.sh rapporto                la tabella (14-rapporto.py)
#
# ⛔⛔ SI ESEGUE SUL TABLET, non sul server — e non e' un dettaglio: i browser
#     sono QUI.  La catena che si misura e' quella vera di Nic:
#     compositore (scatola sul server) → codificatore → filo → Firefox/Chrome
#     sul tablet → il vetro.  ⇒ Il server lo si tocca solo da `ssh`.
#
# ===========================================================================
# ⛔⛔ UNA MISURA ALLA VOLTA, E QUESTA E' LA REGOLA CHE COMANDA TUTTO
# ===========================================================================
# Il tablet e' un CHUWI Hi10 X1: N100 a 4 thread, 7,5 GB.  Due browser che
# decodificano insieme non misurano il prodotto: misurano il tablet.  ⇒ La
# matrice si srotola in fila indiana, e la notte basta perche' e' lunga.
#
# ⭐ L ORDINE: gli scenari CORTI per primi, tutti e tre i desktop e tutt e due i
#   browser, poi i lunghi.  ⛔ Se la notte finisce prima (uno si inchioda, il
#   tablet si spegne, Nic si sveglia presto) abbiamo comunque le risposte
#   principali invece di mezza colonna.
#
# ===========================================================================
# ⛔ IL CONTRATTO CON GLI SCENARI — chi scrive uno scenario nuovo legge QUESTO
# ===========================================================================
# Uno scenario e' un file `scenari/<nome>.py` con dentro:
#
#   NOME      = "pesante"          nome corto, quello che finisce in tabella
#   DURATA_S  = 300                quanto dura UN giro, in secondi (stima)
#   def gira(desktop, marca, nucleo, opzioni) -> dict | int
#
#   `desktop`  "gnome" | "kde" | "xfce"
#   `marca`    "firefox" | "chrome"
#   `nucleo`   il modulo `stress_nucleo` gia' importato
#   `opzioni`  dict: porta, host, dove (cartella degli esiti), secco, tetto_s
#
# ⭐ Lo scenario SCRIVE LA SUA RIGA in `<dove>/esiti.jsonl` — una riga JSON,
#   scritta e chiusa appena il giro finisce.  ⛔ Cosi' un inchiodamento alle tre
#   di notte non porta via anche quel che era gia' stato misurato.
# ⚠ Se non la scrive, la scrive la regia con quel che sa: un giro senza riga
#   sarebbe un giro perso, e un buco in tabella e' indistinguibile da un giro
#   mai partito.
#
# Le chiavi della riga (tutte facoltative tranne le prime quattro):
#   scenario desktop marca esito(0 regge · 1 NON regge · 3 non ho potuto)
#   secondi  perche  consegnati  dipinti  buchi  chiavi_chieste  linee_morte
#   server_prima  server_dopo   (le righe di `11-accendi.sh bilancio`)
#   guasti: [ {gravita: 1..3, che_cosa: "...", riga: "<riga di registro>"} ]
#   registro: percorso del registro salvato · foto: percorso della fotografia
#
# ===========================================================================
# ⛔ QUEL CHE LA REGIA NON FA, DI PROPOSITO
# ===========================================================================
#   · non rifa' le scatole e non ricostruisce il prodotto — la notte serve a
#     misurare `1c592928`, non a cambiarlo sotto i piedi alla misura;
#   · non tocca `nictest` ne' la sua sessione: e' l utente delle prove a mano;
#   · non riavvia i server, tranne dentro lo scenario che esiste per farlo.
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RETE11="$QUI/../11-scatole"
DOVE_SERVER=/media/REMOTIX/tmp/stress
DOVE_QUI=${REMOTIX_STRESS_QUI:-$HOME/.local/state/remotix/stress}
CRED=${REMOTIX_SERVER_SSH:-$HOME/SERVER.ssh}

ok()  { printf '  \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '  \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '      %s\n' "$*"; }
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

SECCO=0
DA_CAPO=0
SCATOLE="gnome kde xfce"
MARCHE="firefox chrome"
SOLO_SCENARIO=""

# ---------------------------------------------------------------------------
# ⭐ Le porte, in un posto solo: la stessa tabella di `11-accendi.sh`.
# ---------------------------------------------------------------------------
porta_di() {
	case "$1" in
	gnome) printf 8511 ;;
	kde)   printf 8512 ;;
	xfce)  printf 8513 ;;
	lxqt)  printf 8514 ;;
	*)     printf 0 ;;
	esac
}

# ---------------------------------------------------------------------------
# ⛔ La parola del server si LEGGE da `~/SERVER.ssh`, non si scrive qui dentro.
#    E' la cura che `credenziali-da-rigenerare` chiede da agosto: un deposito
#    con la parola in chiaro non puo' diventare pubblico.
# ---------------------------------------------------------------------------
HOST=""
PAROLA=""
leggi_credenziali() {
	[ -r "$CRED" ] || { ko "non trovo $CRED: senza quello il server non si raggiunge"; return 1; }
	HOST=$(awk -F: '/^host:/ { gsub(/ /, "", $2); print $2 }' "$CRED")
	PAROLA=$(awk -F: '/^pass:/ { sub(/^[ \t]+/, "", $2); print $2 }' "$CRED")
	[ -n "$HOST" ] || { ko "in $CRED manca la riga host:"; return 1; }
	return 0
}

# ⚠ `ssh -tt` serve perche' `sudo` vuole un terminale; la parola entra dallo
#   standard input e NON compare mai nella riga di comando (la vedrebbe `ps`).
# ⛔⛔ E COL TETTO: `sudo` che chiede la parola a un terminale che non risponde
#     aspetta PER SEMPRE, e una notte intera si ferma li'.  `[M]` 22 set 2026,
#     provato con la parola sbagliata: il giro non finiva piu'.
#     ⇒ 90 secondi e si va avanti; quel che non risponde si dichiara.
sul_server() {
	# ⛔⛔ E LA PAROLA SI TOGLIE DALL USCITA: il terminale la rimanda indietro
	#     come PRIMA RIGA, e chi legge «la prima riga» legge la parola invece
	#     della risposta.  `[M]` 22 set 2026: la sonda della scatola diceva «non
	#     risponde» mentre la scatola rispondeva benissimo.
	#     ⇒ Stessa cura di `fondamenta/strumenti/sshpw.py`: la riga uguale alla
	#       parola non esce.
	printf '%s\n' "$PAROLA" | timeout "${SSH_TETTO:-90}" ssh -tt \
		-o BatchMode=yes -o ConnectTimeout=10 \
		"nicfio@$HOST" "sudo -S -p '' -v 2>/dev/null; $*" 2>/dev/null \
		| tr -d '\r' | grep -v 'tput: No value' | grep -vxF "$PAROLA"
}

# ---------------------------------------------------------------------------
# ⭐⭐ LA SCATOLA SI GUARDA PRIMA, e non e' cerimonia: una misura fatta in una
#     scatola sporca non e' una misura, e' un aneddoto.  `[M]` 22 set 2026: la
#     rete lasciava 22 inquilini e un browser fermo in stato T per scatola.
# ⇒ Tre domande: il server ascolta? c e' qualcuno fermo o zombie? sono rimasti
#   inquilini della rete?  Le ultime due si curano e si DICE che si e' curato.
# ---------------------------------------------------------------------------
SCATOLA_DICE=""

# ⛔⛔ IL COPIONE VIAGGIA IN BASE64, e non e' vezzo: fra `ssh`, `sudo`, `podman
#     exec` e `sh -c` le virgolette si mangiano a vicenda, e un copione che
#     arriva storto non da' un errore — da' una risposta vuota, che si legge
#     come «la scatola non risponde».  `[M]` 22 set 2026: e' successo qui.
dentro_la_scatola() {
	local d=$1 copione=$2 b64
	b64=$(printf '%s' "$copione" | base64 -w0)
	sul_server "echo $b64 | base64 -d | sudo podman exec -i rete11-$d sh -s"
}

scatola_sana() {
	local d=$1 p r ascolta fermi inquilini
	p=$(porta_di "$d")
	SCATOLA_DICE=""
	[ "$SECCO" = 1 ] && { SCATOLA_DICE="(a vuoto) non ho guardato"; return 0; }

	r=$(dentro_la_scatola "$d" "
ss -ltn 2>/dev/null | grep -c :$p
ps -eo stat= | grep -c \"^[TZ]\"
getent passwd | cut -d: -f1 | grep -cE \"^c[0-9]+b?u[0-9]+\$\"
")
	ascolta=$(printf '%s\n' "$r" | sed -n 1p | tr -dc '0-9')
	fermi=$(printf '%s\n' "$r" | sed -n 2p | tr -dc '0-9')
	inquilini=$(printf '%s\n' "$r" | sed -n 3p | tr -dc '0-9')

	if [ -z "$ascolta" ]; then
		SCATOLA_DICE="la scatola rete11-$d non risponde"
		return 1
	fi
	if [ "$ascolta" = 0 ]; then
		SCATOLA_DICE="nessuno ascolta sulla $p"
		return 1
	fi
	if [ "${fermi:-0}" != 0 ] || [ "${inquilini:-0}" != 0 ]; then
		# ⛔ Si pulisce e si DICE: una scatola rimessa in ordine in silenzio
		#    toglie la prova che qualcuno la sporca.
		# ⚠ `[c]3u2` invece di `c3u2`: `pkill -f` pescherebbe anche il guscio
		#   che lo sta eseguendo (22 set 2026, costato un ora).
		dentro_la_scatola "$d" "
for u in \$(getent passwd | cut -d: -f1 | grep -E \"^c[0-9]+b?u[0-9]+\$\"); do
	m=\"runuser -u [\$(printf %s \$u | cut -c1)]\$(printf %s \$u | cut -c2-) \"
	loginctl terminate-user \$u >/dev/null 2>&1
	pkill -CONT -f \"\$m\" >/dev/null 2>&1
	pkill -CONT -u \$u >/dev/null 2>&1
	pkill -KILL -f \"\$m\" >/dev/null 2>&1
	pkill -KILL -u \$u >/dev/null 2>&1
	userdel -r \$u >/dev/null 2>&1 || userdel \$u >/dev/null 2>&1
done
" >/dev/null 2>&1
		SCATOLA_DICE="ripulita prima del giro: ${fermi:-0} processi fermi o zombie, ${inquilini:-0} inquilini della rete rimasti"
		return 0
	fi
	SCATOLA_DICE="pulita"
	return 0
}

bilancio_di() {
	local d=$1
	[ "$SECCO" = 1 ] && { printf 'secco'; return 0; }
	sul_server "cd /media/REMOTIX/rete11 && sudo bash 11-accendi.sh bilancio $d" \
		| grep -E '^(server_pid=|spenta)' | tail -1
}

# ---------------------------------------------------------------------------
# ⭐ I BROWSER DI PROVA SI CHIUDONO, QUELLI DI NIC NO.
#   I banchi aprono profili usa e getta in `/tmp/remotix-ff-*` (Marionette) e
#   `/tmp/remotix-cr-*` (Chrome).  ⇒ Si chiude SOLO chi ha quello nella riga di
#   comando: il Firefox e il Chrome di Nic hanno il profilo in casa loro e non
#   si toccano.
# ⛔ E le parentesi quadre: `pkill -f` pescherebbe anche il guscio che lo sta
#   eseguendo (22 set 2026, costato un ora).
# ---------------------------------------------------------------------------
chiudi_i_browser_di_prova() {
	[ "$SECCO" = 1 ] && return 0
	pkill -f '/tmp/[r]emotix-ff-' >/dev/null 2>&1
	pkill -f '/tmp/[r]emotix-cr-' >/dev/null 2>&1
	sleep 1
	pkill -KILL -f '/tmp/[r]emotix-ff-' >/dev/null 2>&1
	pkill -KILL -f '/tmp/[r]emotix-cr-' >/dev/null 2>&1
	rm -rf /tmp/remotix-ff-* /tmp/remotix-cr-* 2>/dev/null
	return 0
}

# ---------------------------------------------------------------------------
# ⭐⭐ LO SCHERMO DEL TABLET RESTA SVEGLIO, E POI TORNA COM ERA.
# ⛔ `[M]` 22 set 2026: una prova e' morta perche' lo schermo si e' spento e
#    Marionette non ha piu' risposto.  ⇒ Di notte lo schermo non dorme.
# ⚠ E si rimette a mano com era — 600 s, blocco spento — invece di lasciare il
#   tablet cambiato per sempre da un banco.
# ---------------------------------------------------------------------------
schermo_sveglio() {
	[ "$SECCO" = 1 ] && return 0
	gsettings set org.gnome.desktop.session idle-delay 0 2>/dev/null
	gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null
	return 0
}

# ---------------------------------------------------------------------------
# ⭐⭐ LO SCHERMO DEVE ESSERE IL NOSTRO, NON DELL ALTRO UTENTE DEL TABLET.
# ⛔ Misurato il 22 set 2026: se la sessione ATTIVA di `seat0` e' quella
#    dell altro utente (tty3), una finestra nuova non si mappa e Firefox resta
#    appeso a `NewSession` per 180 s — ogni giro col browser visibile muore.
#    ⚠ Una finestra GIA' aperta continua a dipingere: e' solo l apertura che
#      non riesce.  ⇒ Non e' un difetto nostro, e non si cura col codice.
# ⭐ Quindi non si BRUCIA il giro: si ASPETTA, dicendolo, perche' la notte e'
#   ripartibile e un giro rimandato vale piu' di un giro finto.  ⛔ E non si
#   strappa il video a Nic con `loginctl activate`: se sta usando il tablet,
#   comanda lui.
# ---------------------------------------------------------------------------
LA_MIA_SESSIONE=""
la_mia_sessione() {
	[ -n "$LA_MIA_SESSIONE" ] && { printf '%s' "$LA_MIA_SESSIONE"; return 0; }
	LA_MIA_SESSIONE=$(loginctl list-sessions --no-legend 2>/dev/null |
		awk -v u="$(id -un)" '$3==u && $4=="seat0" {print $1; exit}')
	printf '%s' "$LA_MIA_SESSIONE"
}

schermo_e_nostro() {
	local mia attiva
	mia=$(la_mia_sessione)
	[ -z "$mia" ] && return 0            # ⚠ niente seat: non e' il tablet, non giudico
	attiva=$(loginctl show-seat seat0 -p ActiveSession --value 2>/dev/null)
	[ -z "$attiva" ] && return 0
	[ "$attiva" = "$mia" ]
}

# Aspetta che lo schermo torni nostro.  Torna 0 se e' nostro, 1 se ha rinunciato.
ASPETTA_IL_PRIMO_PIANO_MAX=${ASPETTA_IL_PRIMO_PIANO_MAX:-1200}
aspetta_il_primo_piano() {
	[ "$SECCO" = 1 ] && return 0
	schermo_e_nostro && return 0
	local t=0
	inf "lo schermo del tablet e' dell altro utente: aspetto invece di bruciare il giro"
	while [ "$t" -lt "$ASPETTA_IL_PRIMO_PIANO_MAX" ]; do
		sleep 20; t=$(( t + 20 ))
		schermo_e_nostro && { ok "lo schermo e' tornato nostro dopo ${t}s"; return 0; }
		[ $(( t % 300 )) -eq 0 ] && inf "aspetto ancora lo schermo (${t}s)"
	done
	return 1
}

rimetti_lo_schermo() {
	[ "$SECCO" = 1 ] && return 0
	gsettings set org.gnome.desktop.session idle-delay 600 2>/dev/null
	gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null
	inf "schermo del tablet rimesso: idle-delay 600, blocco spento (com era)"
	return 0
}

# ⚠ `wondershaper` lo mette lo scenario della rete strozzata, e la regia si
#   assicura che non resti.  ⛔ Se `sudo` non risponde senza parola non si
#   inventa niente: si DICE, forte, che e' rimasto.
togli_wondershaper() {
	[ "$SECCO" = 1 ] && return 0
	local n
	n=$(ip link show type ifb 2>/dev/null | grep -c '^[0-9]')
	[ "${n:-0}" = 0 ] && return 0
	if sudo -n wondershaper clear wlo1 >/dev/null 2>&1 \
	   || sudo -n wondershaper -c -a wlo1 >/dev/null 2>&1; then
		ok "wondershaper tolto da wlo1"
	else
		ko "⛔ WONDERSHAPER E' RIMASTO SU wlo1 e la rete del tablet e' ancora strozzata"
		inf "toglilo a mano:  sudo wondershaper clear wlo1"
	fi
	return 0
}

# ---------------------------------------------------------------------------
# Gli scenari: chi sono, quanto durano.  ⚠ I metadati si leggono IMPORTANDO il
# file, perche' e' il file stesso la verita'; se non si importa, lo scenario e'
# rotto e lo si dice subito invece di scoprirlo alle tre di notte.
# ---------------------------------------------------------------------------
elenco_scenari() {
	if [ "$SECCO" = 1 ]; then
		printf 'finto 1\n'
		return 0
	fi
	python3 - "$QUI" <<'PY'
import os, sys, importlib.util
qui = sys.argv[1]
cartella = os.path.join(qui, "scenari")
if not os.path.isdir(cartella):
    sys.exit(0)
# ⛔ La cartella degli scenari entra in `sys.path`: fra loro si importano per
#    nome (`_comune`), e caricarli «per percorso» senza questo li romperebbe
#    tutti insieme con un «No module named».
sys.path.insert(0, cartella)
sys.path.insert(0, qui)
for f in sorted(os.listdir(cartella)):
    if not f.endswith(".py") or f.startswith("_"):
        continue
    p = os.path.join(cartella, f)
    try:
        spec = importlib.util.spec_from_file_location(f[:-3], p)
        m = importlib.util.module_from_spec(spec)
        sys.modules[f[:-3]] = m
        spec.loader.exec_module(m)
        nome = getattr(m, "NOME", f[:-3])
        durata = int(getattr(m, "DURATA_S", 300))
        print("%s %d %s" % (nome, durata, p))
    except Exception as e:
        print("ROTTO %s %s: %s" % (f[:-3], p, e))
PY
}

# ---------------------------------------------------------------------------
# ⭐ I giri gia' giudicati non si rifanno — ma un «non ho potuto guardare» SI.
#   ⚠ La differenza conta: 0 e 1 sono risposte, 3 e' una domanda rimasta
#     aperta, e la notte e' lunga abbastanza per riprovarla.
# ---------------------------------------------------------------------------
gia_giudicato() {
	local s=$1 d=$2 m=$3
	[ "$DA_CAPO" = 1 ] && return 1
	[ -r "$DOVE_QUI/esiti.jsonl" ] || return 1
	python3 - "$DOVE_QUI/esiti.jsonl" "$s" "$d" "$m" <<'PY'
import json, sys
percorso, s, d, m = sys.argv[1:5]
for riga in open(percorso, encoding="utf-8", errors="replace"):
    riga = riga.strip()
    if not riga:
        continue
    try:
        r = json.loads(riga)
    except Exception:
        continue
    if (r.get("scenario") == s and r.get("desktop") == d
            and r.get("marca", r.get("browser")) == m
            and r.get("esito") in (0, 1)):
        sys.exit(0)
sys.exit(1)
PY
}

# ---------------------------------------------------------------------------
# UN GIRO.  ⛔ Col suo tetto, e chi lo supera viene ammazzato e si va avanti:
#    una notte che si ferma al primo inchiodamento e' una notte buttata.
# ---------------------------------------------------------------------------
GIRO_ESITO=3
un_giro() {
	local scenario=$1 percorso=$2 durata=$3 d=$4 m=$5
	local tetto t0 t1 secondi
	tetto=$(( durata * 3 / 2 + 180 ))
	t0=$SECONDS
	GIRO_ESITO=3
	# ⭐ Quante righe c erano PRIMA di questo giro: e' cosi' che si riconosce la
	#   riga di questo giro da quelle vecchie — un orologio non basta, perche'
	#   non tutti gli scenari scrivono l ora.
	LINEE_PRIMA=0
	[ -r "$DOVE_QUI/esiti.jsonl" ] && LINEE_PRIMA=$(wc -l < "$DOVE_QUI/esiti.jsonl")

	printf '\n\033[1;34m==> %s · %s · %s\033[0m  (stima %ss, tetto %ss)\n' \
		"$scenario" "$d" "$m" "$durata" "$tetto"

	if ! aspetta_il_primo_piano; then
		ko "$scenario · $d · $m — lo schermo e' rimasto dell altro utente: giro rimandato"
		riga_di_ripiego "$scenario" "$d" "$m" 3 $(( SECONDS - t0 )) \
			"non ho potuto guardare: lo schermo del tablet era dell altro utente"
		return 0
	fi

	if ! scatola_sana "$d"; then
		ko "scatola $d: $SCATOLA_DICE — il giro non parte"
		riga_di_ripiego "$scenario" "$d" "$m" 3 0 "scatola non pronta: $SCATOLA_DICE"
		return 0
	fi
	[ "$SCATOLA_DICE" = "pulita" ] || inf "scatola $d: $SCATOLA_DICE"

	local prima dopo
	prima=$(bilancio_di "$d")

	if [ "$SECCO" = 1 ]; then
		inf "(a vuoto) qui girerebbe $percorso"
		GIRO_ESITO=0
		riga_di_ripiego "$scenario" "$d" "$m" 0 0 "a vuoto"
		return 0
	fi

	# ⛔ Prima ancora di partire: se e' rimasto vivo un Firefox di prova di un
	#   giro andato male (o di una notte interrotta), `NewSession` non risponde
	#   piu' — la finestra si apre e la sessione non arriva mai (22 set 2026,
	#   misurato: tre residui bastano).  ⇒ Si sgombera PRIMA, non solo dopo.
	chiudi_i_browser_di_prova

	timeout -k 20 "$tetto" python3 "$QUI/_lancia.py" \
		--scenario "$percorso" --desktop "$d" --marca "$m" \
		--porta "$(porta_di "$d")" --host "$HOST" \
		--dove "$DOVE_QUI" --tetto "$tetto" --durata "$durata"
	GIRO_ESITO=$?
	t1=$SECONDS
	secondi=$(( t1 - t0 ))

	chiudi_i_browser_di_prova
	dopo=$(bilancio_di "$d")

	case "$GIRO_ESITO" in
	0) ok  "$scenario · $d · $m — regge  (${secondi}s)" ;;
	1) ko  "$scenario · $d · $m — NON REGGE  (${secondi}s)" ;;
	124|137) ko "$scenario · $d · $m — ⛔ SUPERATO IL TETTO di ${tetto}s: ammazzato, si va avanti"
	        salva_il_registro "$d" "$scenario-$m"
	        riga_di_ripiego "$scenario" "$d" "$m" 1 "$secondi" "superato il tetto di ${tetto}s"
	        GIRO_ESITO=1 ;;
	3) inf "?   $scenario · $d · $m — non ho potuto guardare  (${secondi}s)" ;;
	*) inf "?   $scenario · $d · $m — esito $GIRO_ESITO  (${secondi}s)"
	   salva_il_registro "$d" "$scenario-$m" ;;
	esac

	# ⚠ La riga la scrive lo scenario.  Se non c e', la scrive la regia: un giro
	#   senza riga sparirebbe dalla tabella come se non fosse mai partito.
	riga_di_ripiego "$scenario" "$d" "$m" "$GIRO_ESITO" "$secondi" \
		"la riga non l ha scritta lo scenario" "$prima" "$dopo"
	return 0
}

# ⭐ Il registro del server si porta via SOLO quando il giro e' finito male:
#   tenerli tutti vorrebbe dire gigabyte di roba che nessuno legge.
salva_il_registro() {
	local d=$1 come=$2 f
	[ "$SECCO" = 1 ] && return 0
	f="$DOVE_QUI/registri/${d}-${come}-$(date +%H%M%S).log"
	mkdir -p "$DOVE_QUI/registri"
	sul_server "sudo podman exec rete11-$d cat /var/lib/rete11/registro.log" > "$f" 2>/dev/null
	[ -s "$f" ] && inf "registro salvato: $f"
	return 0
}

# ⭐⭐ COMPLETA LA RIGA DEL GIRO, O LA SCRIVE LEI.  Il nome e' rimasto quello
#    vecchio perche' la chiamano in cinque posti, ma adesso fa due cose:
#      · se lo scenario la sua riga l ha scritta, ci AGGIUNGE quel che solo la
#        regia sa — il bilancio del server prima e dopo il giro, e i secondi
#        veri di orologio.  ⛔ Prima li buttava: `crescita()` nel rapporto
#        trovava `server_prima`/`server_dopo` SOLO sulle righe dei giri morti,
#        cioe' proprio dove non servivano (23 set 2026);
#      · se la riga non c e', la scrive lei — e dice scenario, scatola, MARCA
#        del browser e perche'.  ⛔ Un giro morto per strada che non lascia
#        niente domattina somiglia a un giro mai partito.
riga_di_ripiego() {
	# ⛔ A vuoto NON si scrive niente: una riga finta in `esiti.jsonl` sarebbe
	#    una misura che nessuno ha fatto, ed e' peggio di una riga mancante.
	[ "$SECCO" = 1 ] && { inf "(a vuoto) qui scriverei la riga di $1 · $2 · $3"; return 0; }
	python3 - "$DOVE_QUI/esiti.jsonl" "$1" "$2" "$3" "$4" "$5" "$6" "${7:-}" "${8:-}" "${LINEE_PRIMA:-0}" <<'PY'
import json, os, sys, time
percorso, scenario, desktop, marca, esito, secondi, perche = sys.argv[1:8]
prima = sys.argv[8] if len(sys.argv) > 8 else ""
dopo = sys.argv[9] if len(sys.argv) > 9 else ""
linee_prima = int(sys.argv[10]) if len(sys.argv) > 10 and sys.argv[10] else 0
os.makedirs(os.path.dirname(percorso), exist_ok=True)

def completa(r):
    """Quel che solo la regia sa, aggiunto SENZA toccare quel che c e' gia'."""
    cambiato = False
    for chiave, valore in (("server_prima", prima), ("server_dopo", dopo)):
        if valore and not r.get(chiave):
            r[chiave] = valore
            cambiato = True
    # ⚠ I secondi dello scenario contano il suo tetto; questi contano
    #   l orologio della regia (browser acceso e spento compresi): sono due
    #   cose diverse e stanno tutt e due sulla riga.
    if r.get("secondi_della_regia") is None:
        r["secondi_della_regia"] = int(secondi or 0)
        cambiato = True
    if r.get("secondi") is None and secondi:
        r["secondi"] = int(secondi)
        cambiato = True
    if not r.get("browser") and r.get("marca"):
        r["browser"] = r["marca"]
        cambiato = True
    if not r.get("marca") and r.get("browser"):
        r["marca"] = r["browser"]
        cambiato = True
    return cambiato

# ⛔ Se lo scenario la sua riga l ha gia' scritta, la regia NON ne aggiunge una
#    seconda: due righe per lo stesso giro sarebbero due verita' sullo stesso
#    fatto, e la tabella non saprebbe quale credere.  ⇒ La COMPLETA.
# ⭐ «Di questo giro» si riconosce dalla POSIZIONE: le righe nate dopo quelle
#   che c erano all inizio del giro.  ⚠ Non dall orologio, che non tutti
#   scrivono.
if os.path.exists(percorso):
    righe = open(percorso, encoding="utf-8", errors="replace").read().splitlines()
    for n, riga in enumerate(righe):
        if n < linee_prima or not riga.strip():
            continue
        try:
            r = json.loads(riga)
        except Exception:
            continue
        if (r.get("scenario") == scenario and r.get("desktop") == desktop
                and r.get("marca", r.get("browser")) == marca):
            if completa(r):
                righe[n] = json.dumps(r, ensure_ascii=False)
                # ⚠ Si riscrive prima a fianco e poi si sposta: un file di
                #   esiti troncato a meta' notte sarebbe la notte persa.
                accanto = percorso + ".nuovo"
                with open(accanto, "w", encoding="utf-8") as f:
                    f.write("\n".join(righe) + "\n")
                os.replace(accanto, percorso)
            sys.exit(0)
r = {"scenario": scenario, "desktop": desktop,
     "marca": marca, "browser": marca,
     "esito": int(esito), "secondi": int(secondi), "perche": perche,
     "verdetto": {0: "REGGE", 1: "NON REGGE", 3: "non ho potuto guardare"}
                 .get(int(esito), "esito %s" % esito),
     "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
     "quando_finito": time.time(), "scritta_dalla_regia": True}
if prima:
    r["server_prima"] = prima
if dopo:
    r["server_dopo"] = dopo
with open(percorso, "a", encoding="utf-8") as f:
    f.write(json.dumps(r, ensure_ascii=False) + "\n")
PY
	sincronizza
}

# ---------------------------------------------------------------------------
# ⭐ Gli esiti stanno in DUE posti, e non e' ridondanza sprecata: si scrivono
#   sul tablet (dove gira la regia, e dove restano anche se il server sparisce)
#   e si copiano subito in `/media/REMOTIX/tmp/stress/` sul server, che e' il
#   posto dichiarato e quello che sopravvive al riavvio del tablet.
# ---------------------------------------------------------------------------
sincronizza() {
	[ "$SECCO" = 1 ] && return 0
	[ -s "$DOVE_QUI/esiti.jsonl" ] || return 0
	ssh -o BatchMode=yes -o ConnectTimeout=10 "nicfio@$HOST" \
		"mkdir -p $DOVE_SERVER" >/dev/null 2>&1
	scp -q -o BatchMode=yes -o ConnectTimeout=10 \
		"$DOVE_QUI/esiti.jsonl" "nicfio@$HOST:$DOVE_SERVER/esiti.jsonl" >/dev/null 2>&1
	return 0
}

# ---------------------------------------------------------------------------
# LA MATRICE
# ---------------------------------------------------------------------------
gira_tutto() {
	local righe scenario durata percorso d m fatti=0 saltati=0 t0=$SECONDS

	leggi_credenziali || return 2
	mkdir -p "$DOVE_QUI"
	schermo_sveglio
	trap 'printf "\n"; ko "interrotto: rimetto il tablet come lo avevo trovato"; chiudi_i_browser_di_prova; togli_wondershaper; rimetti_lo_schermo; sincronizza; exit 130' INT TERM

	righe=$(elenco_scenari | sort -k2 -n)
	if [ -z "$righe" ]; then
		ko "nessuno scenario in $QUI/scenari: la notte non ha niente da girare"
		rimetti_lo_schermo
		return 2
	fi

	log "la matrice, in ordine di durata (i corti per primi)"
	printf '%s\n' "$righe" | while read -r scenario durata percorso; do
		[ "$scenario" = ROTTO ] && { ko "scenario rotto: $durata $percorso"; continue; }
		inf "$scenario — ${durata}s a giro × $(printf '%s' "$SCATOLE" | wc -w) scatole × $(printf '%s' "$MARCHE" | wc -w) browser"
	done

	while read -r scenario durata percorso; do
		[ -z "$scenario" ] && continue
		if [ "$scenario" = ROTTO ]; then
			ko "scenario rotto, saltato: $durata — $percorso"
			continue
		fi
		[ -n "$SOLO_SCENARIO" ] && [ "$scenario" != "$SOLO_SCENARIO" ] && continue
		for d in $SCATOLE; do
			for m in $MARCHE; do
				if gia_giudicato "$scenario" "$d" "$m"; then
					saltati=$((saltati + 1))
					continue
				fi
				un_giro "$scenario" "$percorso" "$durata" "$d" "$m"
				fatti=$((fatti + 1))
			done
		done
	done <<< "$righe"

	chiudi_i_browser_di_prova
	togli_wondershaper
	rimetti_lo_schermo
	sincronizza
	log "notte finita: $fatti giri fatti, $saltati gia' giudicati e saltati, $(( SECONDS - t0 ))s"
	inf "la tabella:  python3 $QUI/14-rapporto.py"
	return 0
}

# ---------------------------------------------------------------------------
AZIONE=${1:-elenco}
shift 2>/dev/null || true
while [ $# -gt 0 ]; do
	case "$1" in
	--secco)     SECCO=1 ;;
	--da-capo)   DA_CAPO=1 ;;
	--scatola)   SCATOLE=${2:-}; shift ;;
	--marca)     MARCHE=${2:-}; shift ;;
	--scenario)  SOLO_SCENARIO=${2:-}; shift ;;
	*) ko "non conosco $1"; exit 2 ;;
	esac
	shift
done

case "$AZIONE" in
elenco)
	log "gli scenari che trovo"
	elenco_scenari | sort -k2 -n | while read -r nome durata percorso; do
		if [ "$nome" = ROTTO ]; then
			ko "$durata — $percorso"
		else
			inf "$(printf '%-14s' "$nome") ${durata}s a giro · $(( durata * $(printf '%s' "$SCATOLE" | wc -w) * $(printf '%s' "$MARCHE" | wc -w) / 60 )) minuti per tutta la riga"
		fi
	done
	;;
gira)     gira_tutto ;;
rapporto) python3 "$QUI/14-rapporto.py" ;;
*)
	printf 'uso: %s [elenco|gira|rapporto] [--secco] [--scatola "gnome kde"] [--marca firefox] [--scenario nome] [--da-capo]\n' "$0"
	exit 2
	;;
esac
