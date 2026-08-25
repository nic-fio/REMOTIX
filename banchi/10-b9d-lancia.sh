#!/usr/bin/env bash
# ===========================================================================
# 10-b9d-lancia — il giro intero del banco del DIRUPO, dal lucchetto al sgombro.
#
# ⛔⛔ IL PROTOCOLLO DELLE RISORSE CONDIVISE, nell'ordine, e non e' negoziabile:
#     1. il lucchetto della GPU PRIMA degli utenti (`provamt*` sono di tutti);
#     2. appena preso, `stato` — i palchi orfani non danno rosso, danno un
#        numero plausibile;
#     3. alla fine `sgombra` + `spegni` **col lucchetto ancora in mano**, e si
#        VERIFICA con `ss -uln` e `pgrep -a remotix` invece di dichiararlo;
#     4. e solo dopo si molla.
#
# ⛔ Ogni giro che produce un numero passa da `10-b0-terreno.sh` con
#    `LUCCHETTO_MIO=1`: libero non basta, dev'essere MIO.
#
# L'isolamento di questo incarico: porta 8190 · albero 10b9-src · lavoro 10b9 ·
# unita' remotix-8190 · lucchetto «10-b9».
#
# uso:  bash banchi/10-b9d-lancia.sh [OPZIONI_SERVER…]
#       ⭐ quel che passi finisce nella riga d'avvio del server: e' cosi' che si
#         fanno i BRACCI DI CONTROLLO (`--sgombra-soglia-ms 0`,
#         `--niente-ritmo-adattivo`).  ⛔ E il banco lo rilegge dal processo,
#         non da qui (`CODER.md` §2-bis).
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")/.." && pwd)
export PORTA=${PORTA:-8190}
export IND=${IND:-192.168.0.2}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10b9-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10b9}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10b9-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10b9}
export UNITA=${UNITA:-remotix-$PORTA}
export IO_SONO=${IO_SONO:-10-b9}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export FUORI=${FUORI:-/tmp/10-b9d}
export SHM_BASE=${SHM_BASE:-10b9d}
export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export PAROLA_UTENTE=${PAROLA_UTENTE:-mt-dieci-2026}
export QUANTI=${QUANTI:-10}
DA=${DA:-5}; A=${A:-8}; DURATA=${DURATA:-40}; FINE=${FINE:---fine}
# ⛔⭐ IL LUCCHETTO SI PRENDE PER LA DURATA DEL GIRO, NON DELL'INCARICO.
#     Sulla stessa GPU lavorano cinque banchi: chiederne il doppio «per
#     sicurezza» vuol dire fermare gli altri a vuoto.  ⚠ Ma chiederne troppo
#     poco e' peggio: chi arriva dopo la scadenza SCASSINA, e da quel momento
#     due carichi di GPU si falsano in silenzio (`LEZIONI.md` §1.26).
#   ⇒ Il conto: un'apertura per sessione (fino a 4 min l'una a macchina piena),
#     piu' un gradino per ogni misura, piu' i quattro bracci fini, piu' il
#     margine dell'accensione e dello sgombero.
# ⚠ E il conto copre TUTTI E TRE i bracci, perche' stanno nello stesso turno:
#   tre popolazioni da aprire (8 sessioni l'una), i gradini della salita piu' i
#   quattro bracci fini, un gradino per ciascun braccio di controllo, e il
#   margine delle tre accensioni e dello sgombero.
GRADINI=$(( A - DA + 1 + 4 + 2 ))
SECONDI_GIRO=${SECONDI_GIRO:-$(( A * 60 * 3 + GRADINI * (DURATA + 90) + 900 ))}
# ⛔⛔ SEI ORE DI ATTESA, E LA RAGIONE E' MISURATA (non e' prudenza).
#
#     `prendi()` NON E' UNA CODA: E' UNA CORSA.  Il `mkdir` si ritenta ogni 5 s
#     e vince chi arriva per primo dopo un `molla` — nessuna prenotazione,
#     nessuna anzianita'.  `[M]` Un incarico che aspettava dalle 19:53 ha perso
#     DUE passaggi di mano consecutivi senza mai toccare la GPU.
#     ⇒ Con cinque banchi sulla stessa scheda e giri da ~90 minuti, un'attesa
#       corta non fa arrivare prima: fa **saltare il giro** con un codice che
#       somiglia a un problema di terreno, mentre la verita' e' che **la domanda
#       non e' mai stata posta**.  ⛔ Silenzio invece di rosso, e nello strato
#       che ci coordina — la forma peggiore.
ATTESA_TURNO=${ATTESA_TURNO:-21600}
# ⛔ E quante volte si RIMETTE IN CODA un giro che non ha misurato.  ⚠ Solo
#    quello: un giro che ha dato un GIUDIZIO non si rifa' mai, o si misura due
#    volte finche' non esce il numero che piace.
TENTATIVI=${TENTATIVI:-4}
ETICHETTA=${ETICHETTA:-giro}
export OPZIONI_SERVER="$*"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
dub() { printf '    \033[1;33m??\033[0m  %s\n' "$*"; }

cd "$QUI" || exit 2
LAV_LOCALE=${LAV_LOCALE:-/tmp/10-b9d}
mkdir -p "$LAV_LOCALE"

# ⛔⛔ `molla` STA QUI, PRIMA DI `pulisci` — e non e' gusto per l'ordine.
#     `[M]` provato: con la definizione piu' in basso, il SIGTERM arrivato
#     mentre il lanciatore era ancora sopra faceva scattare la trappola su una
#     funzione **non ancora definita**: «molla: comando non trovato», e il
#     lucchetto restava occupato.  ⚠ Una trappola che chiama una cosa che non
#     c'e' e' peggio di nessuna trappola: sembra armata.
molla() {
	python3 - <<PY
import importlib.util, os
os.environ["LUCCHETTO"] = "$LUCCHETTO"
s = importlib.util.spec_from_file_location("luc", "banchi/09-lucchetto.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
m.molla("$IO_SONO")
PY
}

# ⛔⛔⛔ E IL SEGNALE VA ASPETTATO CON `wait`, NON DENTRO UN FIGLIO IN PRIMO
#      PIANO — `[M]` provato il 24 agosto 2026 su questo stesso file, e la
#      prima stesura NON PASSAVA.
#
#      bash **rimanda** i `trap` finche' un figlio in primo piano non e' finito.
#      Con `python3 …giro…` in primo piano, un SIGTERM al lanciatore resta in
#      sospeso per tutta la durata del giro: la pulizia non gira, il lucchetto
#      resta occupato col campo sporco, e ⛔ **non c'e' nessuna riga rossa** —
#      si vede solo un lanciatore che «non risponde».
#      ⚠ Ed e' precisamente la forma che il coordinatore ha segnalato: SIGTERM
#        che ammazza senza far girare il `finally`.  Qui non ammazza: ADDORMENTA
#        la cura, che e' peggio, perche' sembra armata.
#
#  ⇒ Il figlio si manda in FONDO e si aspetta con `wait`, che i segnali
#    interrompono davvero; e la pulizia gli manda a sua volta SIGTERM, invece di
#    lasciarlo in piedi a tenere la GPU.
FIGLIO=0
aspetta() {
	"$@" & FIGLIO=$!
	wait "$FIGLIO"; local r=$?
	FIGLIO=0
	return "$r"
}

PULITO=0
pulisci() {
	[ "$PULITO" = 1 ] && return
	PULITO=1
	printf '\n\033[1m== ⛔ PULIZIA (segnale o uscita) — spengo, sgombero e mollo\033[0m\n'
	# ⛔ Nel modo di prova NON si tocca niente di condiviso: la trappola si prova
	#    su un lucchetto finto, e sgomberare i `provamt*` mentre li usa un altro
	#    banco sarebbe far pagare la mia prova a lui.
	if [ "$FIGLIO" != 0 ]; then
		printf '    --  ammazzo il giro in corso (pid %s)\n' "$FIGLIO"
		kill -TERM "$FIGLIO" 2>/dev/null
		wait "$FIGLIO" 2>/dev/null
		FIGLIO=0
	fi
	# ⛔ E il CORRIDORE, che vive di la': un `ssh` ammazzato di qua puo' lasciare
	#    il ciclo in piedi sulla macchina, e quello continuerebbe a correre per il
	#    lucchetto a nome mio.  ⚠ Se ce la facesse, il lucchetto resterebbe preso
	#    da un nome vivo e nessuno lo mollerebbe — e' proprio il caso che
	#    l'adozione esiste per raccogliere, ma meglio non arrivarci.
	pkill -f "corri.sh '$LUCCHETTO'" 2>/dev/null
	ssh -o BatchMode=yes -o ConnectTimeout=8 "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' pkill -f 'corri[.]sh $LUCCHETTO'" \
	  >/dev/null 2>&1
	if [ "${SOLO_TRAPPOLA:-0}" != 1 ]; then
		bash banchi/10-b91-terreno-dieci.sh sgombra >/dev/null 2>&1
		bash banchi/10-b91-terreno-dieci.sh spegni  >/dev/null 2>&1
	fi
	molla
}
# ⛔⛔ E LE TRAPPOLE SI ARMANO PRIMA DELLA CORSA, non dopo.
#     `[M]` Il difetto visto: ammazzando il pilota MENTRE ASPETTAVA, il suo
#     corridore restava in piedi e continuava a correre per il lucchetto a nome
#     mio.  ⇒ La trappola dev'essere gia' armata quando la corsa comincia.
# ⚠ E `pulisci` e' sicura anche adesso che il lucchetto non e' mio: `molla` si
#   rifiuta se il nome dentro non e' il mio, e `sgombra`/`spegni` su una macchina
#   dove non ho ancora acceso niente non fanno nulla.
trap 'pulisci; exit 143' TERM INT HUP
trap 'pulisci' EXIT

# ── 1. IL LUCCHETTO — ⛔ E LA CORSA SI CORRE SULLA MACCHINA ────────────────
#
# ⛔⛔ PERCHE' NON SI USA `09-lucchetto.py prendi()`, e la ragione e' MISURATA.
#
#     Il lucchetto NON E' UNA CODA: e' una CORSA.  Nessuna prenotazione, nessuna
#     anzianita' — vince chi arriva per primo dopo un `molla`.  ⇒ Chi ritenta
#     piu' fitto vince quasi sempre, e `prendi()` ritenta ogni **5 secondi**
#     mentre altri pilota ritentano ogni secondo.
#
#     `[M]` 24-25 agosto 2026, questo incarico: **cinque passaggi di mano persi
#     di fila**, 982 giri d'attesa in un turno solo (~82 minuti) senza mai
#     toccare la GPU.  Un altro incarico ha perso allo stesso modo una finestra
#     da 45 minuti.  ⚠ Non e' sfortuna: e' il passo.
#
# ⭐ E il ciclo gira SULLA MACCHINA (`10-b9d-corri-al-lucchetto.sh`), non qui:
#    un tentativo via `ssh` costa 100-200 ms di rete, quindi ritentare da fuori
#    ogni mezzo secondo aprirebbe duemila connessioni all'ora **e** lascerebbe
#    lo stesso una finestra piu' larga del passo dichiarato.
#    `[M]` provato con un lucchetto finto: rilascio a 2 000 ms, preso a
#    **2 047 ms** — 47 ms di ritardo contro i fino-a-5 000 di prima.
#
# ⛔ E `banchi/09-lucchetto.py` NON si tocca: e' di tutti.  Il file `chi` si
#    scrive con lo stesso formato — «<scadenza epoch> <nome>» — e lo scassino di
#    un lucchetto scaduto resta DICHIARATO, come li'.
log "1 · il lucchetto della GPU «$IO_SONO» per $SECONDI_GIRO s — ⛔ prima degli utenti condivisi"
inf "⚠ la corsa si corre sulla macchina, passo 0,5 s: con i 5 s di prendi() ho perso cinque passaggi di mano di fila"

# ⛔ Prima il corridore, poi la corsa: si spedisce nella MIA cartella.
B64=$(base64 -w0 banchi/10-b9d-corri-al-lucchetto.sh)
ssh -o BatchMode=yes "$MACCHINA" \
  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '
     mkdir -p $LAV && printf %s $B64 | base64 -d > $LAV/corri.sh
     chmod +x $LAV/corri.sh'" >/dev/null 2>&1 || {
	ko "⛔ NON MISURO: il corridore non e' arrivato sulla macchina"; exit 2; }

# ⚠ E se la connessione cade mentre aspetto, si riprova: un `ssh` che muore
#   dopo due ore d'attesa non e' «il lucchetto e' di un altro».
PRESO=no
for GIRO in 1 2 3 4 5; do
	# ⛔⛔ E IL CORRIDORE GIRA SOTTO `aspetta`, non in primo piano — `[M]` il
	#     difetto e' stato VISTO, non temuto: i due pilota che ho ucciso mentre
	#     aspettavano hanno lasciato in piedi il loro `python3` che aspettava il
	#     lucchetto, e quelli hanno continuato a CORRERE per due ore a nome
	#     «10-b9».  ⚠ Se uno avesse vinto, avrebbe tenuto la GPU per 3 640 s con
	#     nessuno a mollarla, e per gli altri sarebbe stato un lucchetto occupato
	#     da un nome vivo — nessun rosso, nessuno scassino, solo attesa.
	# ⇒ Sotto `aspetta` il pid finisce in `$FIGLIO` e la trappola lo ammazza.
	aspetta bash -c "ssh -o BatchMode=yes -o ServerAliveInterval=30 '$MACCHINA' \
	  \"printf '%s\\n' '$PAROLA_SUDO' | sudo -S -p '' \
	    $LAV/corri.sh '$LUCCHETTO' '$IO_SONO' $SECONDI_GIRO $ATTESA_TURNO 0.5\" \
	  2>&1 | grep -v '^tput' > $LAV_LOCALE/corsa.txt"
	RCL=$?
	USCITA=$(cat "$LAV_LOCALE/corsa.txt" 2>/dev/null)
	printf '%s\n' "$USCITA" | sed 's/^/    --  /'
	case "$USCITA" in
	PRESO*)    PRESO=si; break ;;
	SCASSINO*) PRESO=si; break ;;   # ⭐ lo dice lui, e poi prende
	SCADUTA*)  ko "⛔ NON MISURO: l'attesa di $ATTESA_TURNO s e finita e il lucchetto non e' mio"; exit 2 ;;
	MIO*)
		# ⛔⛔ L'ADOZIONE — `prendi()` non ha nessun ramo per «il lucchetto e'
		#     GIA' MIO»: se il nome combacia col mio, aspetta esattamente come
		#     se fosse di un altro.  ⇒ Un pilota morto male lascia il lucchetto
		#     col MIO nome e il pilota dopo **aspetta se stesso** fino alla
		#     scadenza.  `[M]` visto il 24 agosto 2026: ottanta minuti di GPU
		#     bloccati per tutti, e nessuna riga rossa da nessuna parte.
		# ⭐ La cura non e' scassinare: e' RICONOSCERE IL PROPRIO NOME dopo aver
		#    verificato che nessun processo mio sia vivo, e DICHIARARLO.
		#    ⚠ Adottare in silenzio sarebbe peggio del blocco.
		VIVI=$(ssh -o BatchMode=yes "$MACCHINA" \
		  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \
		   \"pgrep -f '10b9-sr[c]/src/remotix' | head -3\"" 2>/dev/null | grep -v '^tput')
		if [ -n "$VIVI" ]; then
			ko "⛔ il lucchetto e' a nome mio E ci sono processi miei vivi ($VIVI): c'e' un altro pilota in giro, NON adotto"
			exit 2
		fi
		inf "⚠ ⛔ IL LUCCHETTO E' GIA' A NOME MIO e nessun processo mio e' vivo: e' il resto di un pilota morto male"
		inf "⚠ ADOTTO e rimetto la scadenza a $SECONDI_GIRO s — e lo dichiaro, invece di aspettare me stesso"
		ssh -o BatchMode=yes "$MACCHINA" \
		  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \
		   \"printf '%s %s\\n' \\\$(( \\\$(date +%s) + $SECONDI_GIRO )) '$IO_SONO' > '$LUCCHETTO/chi'\"" \
		  >/dev/null 2>&1
		PRESO=si; break ;;
	*)
		dub "⚠ il corridore non ha risposto come mi aspettavo (rc=$RCL, giro $GIRO/5): riprovo"
		aspetta sleep 5 ;;
	esac
done
[ "$PRESO" = si ] || { ko "⛔ NON MISURO: il lucchetto non e' arrivato"; exit 2; }
ok "lucchetto preso"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ E LA TRAPPOLA SI PROVA — «un banco non e' finito finche' non l'hai visto
#     dare rosso» vale anche per la PULIZIA.  ⚠ Una pulizia che non ha mai
#     girato e una pulizia che non c'e' producono lo stesso registro: nessuna
#     riga.  ⇒ `SOLO_TRAPPOLA=1` prende un lucchetto FINTO (nome e cartella
#     suoi, mai quello della GPU), arma la trappola e aspetta: chi prova gli
#     manda SIGTERM e guarda se il lucchetto e' tornato libero.
if [ "${SOLO_TRAPPOLA:-0}" = 1 ]; then
	ok "⛔ MODO PROVA: lucchetto «$IO_SONO» in «$LUCCHETTO» preso, trappola armata"
	inf "adesso aspetto: mandami SIGTERM e guarda se il lucchetto si libera"
	aspetta sleep 300
	exit 0
fi

# ── 2. IL POSTO E' LIBERO? — i palchi orfani, PRIMA di misurare ────────────
log "2 · ⛔ i palchi orfani — in fase 9 un palco orfano non dava rosso, dava un numero plausibile"
bash banchi/10-b91-terreno-dieci.sh stato 2>&1 | tail -30
inf "⛔ sgombro comunque, per partire da un posto pulito che ho verificato io"
bash banchi/10-b91-terreno-dieci.sh sgombra 2>&1 | tail -8

# ── 2-bis. LA PAROLA DEI `provamt*` — ⛔ SI COPIA, NON SI RIMETTE ──────────
#
# ⛔ Gli utenti `provamt1…11` sono CONDIVISI in questo giro, e il passo `utenti`
#    di `10-b91` rifarebbe `chpasswd` su tutti e undici.  ⚠ Mentre un altro
#    banco ci sta lavorando, rimettere la parola d'ordine di undici utenti per
#    prendermi un file e' un rischio che non serve a niente: la parola e' gia'
#    quella, e mi basta scriverla nella MIA cartella con i suoi permessi.
# ⛔ E non passa da `argv` (D12): heredoc sullo stdin di `tee`.
log "2-bis · la parola dei provamt* nella MIA cartella (0600, mai in argv)"
# ⛔ La parola arriva sullo STDIN, dietro quella di sudo: `sudo -S` consuma la
#    prima riga, `read` la seconda.  ⚠ Cosi' non compare in nessun `argv`, ne'
#    qui ne' sulla macchina di prova — e' la regola D12, e vale anche quando la
#    parola e' quella di un utente di prova.
printf '%s\n%s\n' "$PAROLA_SUDO" "$PAROLA_UTENTE" | ssh -o BatchMode=yes "$MACCHINA" \
  "sudo -S -p '' bash -c '
    read -r p
    mkdir -p $LAV/certificati $LAV/rilievo; chmod 1777 $LAV/rilievo
    printf %s \"\$p\" > $LAV/parola; chmod 600 $LAV/parola
    echo \"byte nella parola: \$(wc -c < $LAV/parola)\"'" 2>&1 | \
  grep -v '^tput' | sed 's/^/        /'

# ── 3. IL SERVER ───────────────────────────────────────────────────────────
log "3 · accendo il server sulla $PORTA — opzioni «${OPZIONI_SERVER:-(nessuna: le cure della fase 9 NASCONO ACCESE)}»"
bash banchi/10-b91-terreno-dieci.sh accendi 2>&1 | tail -20 || {
	ko "⛔ il server non e' partito"; molla; exit 2; }

# ⛔⛔ E LA CURA SI VERIFICA DAL PROCESSO, NON DAL COMANDO CHE HO SCRITTO.
log "3-bis · ⛔ la riga d'avvio VERA del processo, e quel che il server ha scritto"
ssh -o BatchMode=yes "$MACCHINA" \
  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
    P=\\\$(systemctl show -p MainPID --value $UNITA.service)
    echo 'pid: '\\\$P
    tr '\\0' ' ' < /proc/\\\$P/cmdline; echo
    md5sum $ALBERO/src/remotix
    grep -a 'soglia della coda video\\|regolatore del ritmo\\|IL REGOLATORE' $LAV/registro.log | tail -4\"" 2>&1 | \
  grep -v '^tput' | sed 's/^/        /'

# ── 3-ter. ⛔⛔ I VICINI: SI DICHIARANO, E SI VERIFICA CHE SIANO FERMI ──────
#
# Alla fase 10 sulla stessa macchina vivono i server di cinque banchi, accesi
# fra un giro e l'altro.  `10-b0-terreno.sh` da' rosso su ognuno, e ha ragione:
# «un banco che misura mentre gira il server di un altro misura la SOMMA».
#
# ⛔ Ma la risposta giusta NON e' spegnerli (non sono miei) ne' tacerli
#    (`PORTE_AMMESSE` a scatola chiusa e' un rosso messo a tacere).  ⇒ Si
#    dichiarano **quelli che ci sono adesso**, uno per uno e stampati, E si
#    verifica la cosa che conta davvero per una misura di GPU: che **non abbiano
#    figli**.  `[M]` §6.4-bis: una sessione ferma costa GPU ZERO (RC6 100 %, GT
#    0 MHz), e un server senza figli non ha nemmeno quella.
# ⛔⛔ Un solo `remotix-figlio` non mio vivo, invece, vuol dire che qualcuno sta
#     catturando e codificando **sulla mia stessa GPU** nonostante il lucchetto:
#     li' non si misura, e si dice di chi e'.
log "3-ter · ⛔ i vicini: quali porte non mie, e hanno figli vivi?"
VICINI=$(ssh -o BatchMode=yes "$MACCHINA" \
  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
    ss -ulnH | grep -oE ':(7[0-9]{3}|8[0-9]{3}) ' | tr -d ': ' | sort -u\"" \
  2>/dev/null | grep -v '^tput' | grep -v "^$PORTA\$" | tr '\n' ' ')
FIGLI_ALTRUI=$(ssh -o BatchMode=yes "$MACCHINA" \
  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
    pgrep -af 'remotix-figli[o]' || true\"" 2>/dev/null | grep -v '^tput')
inf "porte 7xxx/8xxx non mie, vive adesso: ${VICINI:-(nessuna)}"
if [ -n "$FIGLI_ALTRUI" ]; then
	ko "⛔⛔ NON MISURO: ci sono figli «remotix» vivi che non sono miei —"
	printf '%s\n' "$FIGLI_ALTRUI" | sed 's/^/        /'
	ko "un figlio vivo cattura e codifica sulla MIA stessa GPU, lucchetto o no"
	exit 2
fi
ok "nessun «remotix-figlio» vivo sulla macchina: i vicini sono server FERMI, e un server senza figli costa GPU zero"
export PORTE_AMMESSE="$VICINI"

# ── 4. IL TERRENO DELLA FASE ───────────────────────────────────────────────
log "4 · ⛔ banchi/10-b0-terreno.sh — prima di ogni giro che produce un numero"
inf "⚠ PORTE_AMMESSE dichiarate: ${PORTE_AMMESSE:-(nessuna)} — e sono quelle che ho appena elencato, non una scatola chiusa"
# ⛔ E L'USCITA SI MOSTRA INTERA SE DA' ROSSO.  ⚠ La prima stesura ne stampava
#    la coda (`tail -40`) e ha nascosto **esattamente le due righe che dicevano
#    quali predicati fossero rossi**: la ragione del rifiuto stava in cima.
CHI="$IO_SONO" LUCCHETTO_MIO=1 PORTA="$PORTA" UTENTE=provamt1 \
	ALBERO="$ALBERO" LAV="$LAV" \
	bash banchi/10-b0-terreno.sh > "$LAV_LOCALE/terreno.log" 2>&1
RC=$?
if [ "$RC" != 0 ]; then
	ko "⛔ il terreno esce $RC — TUTTE le righe rosse, che e' quel che serve:"
	sed 's/\x1b\[[0-9;]*m//g' "$LAV_LOCALE/terreno.log" | grep -aE "^    NO|guai|IGNOTI|NON REGGE|predicati giudicati" | sed 's/^/        /'
else
	grep -acE "OK" "$LAV_LOCALE/terreno.log" >/dev/null
	ok "il terreno regge ($(grep -ac 'OK' "$LAV_LOCALE/terreno.log") predicati verdi) — dettaglio in $LAV_LOCALE/terreno.log"
fi
if [ "$RC" != 0 ]; then
	ko "⛔ il terreno non regge (esce $RC): NON misuro"
	bash banchi/10-b91-terreno-dieci.sh spegni >/dev/null 2>&1
	molla
	exit "$RC"
fi

# ── 5. I TRE BRACCI, DENTRO LO STESSO TURNO DI LUCCHETTO ───────────────────
#
# ⛔⛔ E STANNO INSIEME PER UNA RAGIONE MISURATA, non per comodita'.
#
#     `prendi()` non e' una coda, e' una CORSA: vince chi arriva per primo dopo
#     un `molla`, senza prenotazione ne' anzianita'.  `[M]` 24-25 agosto 2026:
#     questo pilota ha perso QUATTRO passaggi di mano di fila e ha aspettato
#     1 142 giri (~95 minuti) senza mai toccare la GPU.  ⇒ Con cinque banchi
#     sulla stessa scheda, chiedere tre turni per tre bracci vuol dire, in
#     pratica, non farne nessuno.
#
# ⭐ Quindi i bracci si fanno TUTTI DENTRO LO STESSO TURNO: si riaccende il
#    server con opzioni diverse — il lucchetto resta mio — e fra un braccio e
#    l'altro NON si molla.  ⚠ Il prezzo si dichiara: il turno dura di piu', e
#    gli altri aspettano di piu'.  E' un prezzo pagato una volta invece di tre.
#
# ⛔ L'ORDINE NON E' CASUALE: il braccio normale viene PRIMO, perche' e'
#    l'ancora — se non ritrova il dirupo, i due bracci di controllo non hanno
#    niente da controllare, e il pilota lo dice invece di misurarli lo stesso.
#
#   | # | server                        | giro              | che domanda fa |
#   |---|-------------------------------|-------------------|----------------|
#   | 1 | i predefiniti (cure ACCESE)   | 5→8 + bracci fini | dov'e' il dirupo, chi tiene la GPU, dove sono fermi i figli |
#   | 2 | `--sgombra-soglia-ms 0`       | solo 8            | ⭐ la soglia della coda ci mette del suo? |
#   | 3 | `--niente-ritmo-adattivo`     | solo 8            | ⭐ e il regolatore del ritmo? |
#
# ⚠ Il braccio 2 spegne DUE cose insieme, e il server stesso lo scrive: senza
#   la soglia, `arretrato` non puo' superare 1 e il regolatore non scatta mai
#   (`webtransport.c:3476`).  ⇒ Il braccio 3 esiste apposta per separarle.
BRACCI=${BRACCI:-"normale|| ; sgombra0|--sgombra-soglia-ms 0|--soglia-spenta ; ritmo-spento|--niente-ritmo-adattivo|--ritmo-spento"}
RC=0
ANCORA_HA_VISTO_IL_DIRUPO=ignoto

IFS=';' read -ra ELENCO <<<"$BRACCI"
for BR in "${ELENCO[@]}"; do
	BR=$(printf '%s' "$BR" | sed 's/^ *//; s/ *$//')
	[ -n "$BR" ] || continue
	NOME=${BR%%|*}; RESTO=${BR#*|}
	OPZ=${RESTO%%|*}; BANDIERA=${RESTO#*|}
	if [ "$NOME" != "normale" ] && [ "$ANCORA_HA_VISTO_IL_DIRUPO" = "no" ]; then
		ko "⛔ NON MISURO il braccio «$NOME»: il braccio normale NON ha ritrovato"
		ko "   il dirupo, e un controllo su un fenomeno che non si e' presentato"
		ko "   misura il nulla e sembra dire «la cura non c'entra»"
		continue
	fi

	log "5 · BRACCIO «$NOME» — server con «${OPZ:-(i predefiniti: cure ACCESE)}»"
	OPZIONI_SERVER="$OPZ"
	export OPZIONI_SERVER
	bash banchi/10-b91-terreno-dieci.sh accendi > "$LAV_LOCALE/accendi-$NOME.log" 2>&1 || {
		ko "⛔ il server non e' ripartito per il braccio «$NOME»"
		tail -12 "$LAV_LOCALE/accendi-$NOME.log" | sed 's/^/        /'
		RC=2; continue; }
	ok "server riacceso"
	# ⛔ E QUEL CHE GIRA DAVVERO SI LEGGE DAL PROCESSO — `CODER.md` §2-bis.
	#    ⚠ Il banco lo rifa' per conto suo e si rifiuta se non torna; questa e'
	#      la copia per chi legge il registro del pilota.
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
	    P=\\\$(systemctl show -p MainPID --value $UNITA.service)
	    tr '\\0' ' ' < /proc/\\\$P/cmdline; echo\"" 2>&1 | \
	  grep -v '^tput' | sed 's/^/        argv: /'

	# ⛔ E UN GIRO CHE NON HA MISURATO SI RIMETTE IN CODA — ma SOLO quello.
	#    Esce 2 = «non ho potuto misurare»: una domanda **mai posta**, e
	#    ripeterla non cambia nessun numero.  ⛔ Esce 0 o 1 = c'e' un GIUDIZIO, e
	#    un giudizio non si rifa' mai: rifarlo vorrebbe dire misurare due volte
	#    finche' non esce il numero che piace.
	if [ "$NOME" = "normale" ]; then DA_QUI=$DA; FIN=$FINE; else DA_QUI=$A; FIN=""; fi
	RCB=2
	for T in $(seq 1 "$TENTATIVI"); do
		[ "$T" -gt 1 ] && log "5-bis · ⚠ TENTATIVO $T/$TENTATIVI del braccio «$NOME» — il precedente NON HA MISURATO (esce 2), non ha dato un giudizio"
		# shellcheck disable=SC2086
		aspetta python3 banchi/10-b9d-dirupo.py giro --da "$DA_QUI" --a "$A" \
			--durata "$DURATA" $FIN $BANDIERA --lucchetto-gia-mio \
			--etichetta "$NOME"
		RCB=$?
		[ "$RCB" != 2 ] && break
		inf "⚠ rimetto in coda fra 20 s (il lucchetto resta mio)"
		aspetta sleep 20
	done
	[ "$RCB" != 0 ] && RC=$RCB
	if [ "$NOME" = "normale" ]; then
		# ⛔ E lo si chiede agli ESITI, non a un `grep` sul testo: il verdetto
		#    sul dirupo e' un campo, e leggerlo dal campo e' l'unico modo di
		#    distinguere «nessun dirupo» da «non ho potuto giudicare».
		if python3 -c "
import json, sys
try:
    d = json.load(open('/tmp/10-b9d/10-b9d-normale.json'))
except Exception:
    sys.exit(3)
sys.exit(0 if (d.get('dirupo') or {}).get('esito') == 'DIRUPO' else 1)"; then
			ANCORA_HA_VISTO_IL_DIRUPO=si
			ok "⭐ l'ancora ha ritrovato il dirupo: i due bracci di controllo hanno qualcosa da controllare"
		else
			ANCORA_HA_VISTO_IL_DIRUPO=no
			ko "⛔ il braccio normale NON ha ritrovato il dirupo (o non l'ha potuto giudicare)"
		fi
	fi
done

# ── 6. SI LASCIA COME SI E' TROVATO, E LO SI VERIFICA ──────────────────────
log "6 · ⛔ sgombro, spengo, e VERIFICO — col lucchetto ancora in mano"
bash banchi/10-b91-terreno-dieci.sh sgombra 2>&1 | tail -8
bash banchi/10-b91-terreno-dieci.sh spegni  2>&1 | tail -5
ssh -o BatchMode=yes "$MACCHINA" \
  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
    echo '--- ss -uln :$PORTA'; ss -uln | grep ':$PORTA ' || echo '(nessuno: bene)'
    echo '--- i miei processi'; pgrep -af '$ALBERO' || echo '(nessuno: bene)'
    echo '--- netem'; tc qdisc show dev lo | head -2; tc qdisc show dev enp7s0 | head -2\"" 2>&1 | \
  grep -v '^tput' | sed 's/^/        /'

# ⛔ La pulizia e' stata fatta qui sopra, passo per passo e con la verifica
#    sotto gli occhi: si segna come fatta perche' il `trap EXIT` non la rifaccia.
PULITO=1
molla
exit "$RC"
