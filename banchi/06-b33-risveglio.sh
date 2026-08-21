#!/bin/bash
#
# 06-b33-risveglio.sh — ⛔⛔ LA SECONDA PORTA DEL CLIC CHE MUORE, §7.1.
#
#   ⚠ GIRA SUL SERVER (192.168.0.2), come utente `nicfio`, NON da root e NON
#     dentro il contenitore.
#
#   bash 06-b33-risveglio.sh <file-parola-sudo> tutto
#   bash 06-b33-risveglio.sh <file-parola-sudo> strumento  ⭐ il controllo ZERO
#   bash 06-b33-risveglio.sh <file-parola-sudo> libero     3 risvegli, mano alzata
#   bash 06-b33-risveglio.sh <file-parola-sudo> tenuto     ⛔ LA SCENA CATTIVA
#   bash 06-b33-risveglio.sh <file-parola-sudo> confronto  la porta GIA' NOTA
#
# ===========================================================================
# ⛔ L'ATTESO, DICHIARATO PRIMA — `CODER.md` §3.3
# ===========================================================================
#
# La tesi di §7.1 che questo banco parte per SMENTIRE:
#
#   *«ogni `cattura_risveglia()` (400 ms, scena ferma, chiave dovuta) ricrea i
#     dispositivi di `libei`: 3 risvegli, 3 ricambi, con zero `ADATTA_TELA`»*
#
# S0 · strumento   il testimone vede `BTN_LEFT` giu' E su, senza nessun
#                  ricambio in mezzo.  ⛔ Se non li vede, tutto il resto e' IL
#                  BANCO e non il prodotto
# S1 · libero      3 `risveglia`, **niente premuto** ⇒ `ricambi_puntatore`
#                  atteso **+3** (uno per risveglio) e **zero** chiamate a
#                  `cattura_ridimensiona()`.  ⚠ Se il delta fosse 0, §7.1 e'
#                  FALSA e va corretta — ed e' l'esito che questo banco deve
#                  poter dichiarare
# S2 · tenuto      `BTN_LEFT` giu' → **un solo** `risveglia` → si rilascia.
#                  atteso col mondo di oggi: ⛔ il rilascio **NON arriva** al
#                  testimone, e il clic FRESCO successivo **non arriva
#                  nemmeno lui** (il posto conta il pulsante ancora giu',
#                  `meta-seat-impl.c:899-908`).  ⭐ E il TASTO invece arriva:
#                  la tastiera non e' un dispositivo di viewport
# S3 · confronto   la stessa scena con `ridimensiona` al posto di `risveglia`:
#                  e' la porta gia' misurata da §4.6.  ⛔ Serve a distinguere
#                  «il risveglio ricambia» da «ricambia tutto sempre»: senza
#                  questo confronto il numero di S2 non significa niente
#
# ===========================================================================
# ⛔⛔ IL LIMITE, IN TESTA PERCHE' NESSUNO CI CADA IN VERDE
# ===========================================================================
#
# **Qui non c'e' il server**: non c'e' QUIC, non c'e' `rcp.c`, non c'e' la
# pagina.  C'e' `06-b33-risveglio`, che collega `src/cattura.c` e `src/input.c`
# e li chiama da riga di comando (`CODER.md` §3.6).
#
#   ⇒ ⛔ Questo banco NON PUO' DIRE se il PRODOTTO cade in questa scena: dice
#     che **la funzione che il prodotto chiama** ci cade.  Il passo dal secondo
#     al primo lo fa `figlio.c:6365`, che chiama `cattura_risveglia()` quando la
#     presa e' ZERO e una chiave e' dovuta — cioe' **su un desktop fermo**, che
#     e' esattamente la scena qui sotto.  ⚠ Ma il giro col server vero e' un
#     altro banco, e finche' non c'e' la marca resta `[M] sul modulo`.
#
#   ⇒ E NON DICE NIENTE sul browser: nessun quadro, nessun `requestAnimationFrame`.
#
# ⚠ Ogni misura di tempo porta accanto il CARICO: dieci agenti sulla stessa
#   macchina, e un numero preso sotto carico e non dichiarato tale e' un numero
#   falso.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?serve il file 0600 con la parola di sudo}
COSA=${2:-tutto}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
T=$SRC/banchi/06-b33-terreno.sh
G=$SRC/banchi/06-b33-risveglio-giudice.py
ESITI=$LAV/06-b33-risveglio-esiti.jsonl
TELA=${TELA:-1264x800}
TELA2=${TELA2:-1000x640}
TL=${TELA%x*}
TA=${TELA#*x}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { printf '⛔ %s non si legge\n' "$PAROLA_SUDO"; exit 2; }
sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
terreno()  { sudo_mio bash "$T" "$@"; }
di()       { terreno iniettore-di "$@" >/dev/null; }
carico()   { terreno carico | sed 's/^/        /'; }

# ⛔ La scena si rimonta da capo a OGNI giro, e il motivo e' misurato: una volta
#    che il posto ha un pulsante bloccato giu', l'unica cosa che lo sblocca e'
#    la caduta del canale EIS (`meta-eis-client.c:1075`, `drop_device`).  ⇒ Un
#    secondo giro dentro lo stesso iniettore misurerebbe il DANNO DEL PRIMO.
rimonta() {
	terreno iniettore-spegni  > /dev/null 2>&1
	terreno testimone-via     > /dev/null 2>&1
	terreno spegni            > /dev/null 2>&1
	sleep 2
	terreno sessione > /dev/null 2>&1
	terreno iniettore-accendi "$TELA" || return 3
	# ⛔ Il testimone si apre DOPO l'iniettore: e' l'iniettore che monta il
	#    monitor virtuale, e il testimone lo sceglie PER MISURA.  Aprirlo prima
	#    vorrebbe dire cercare uno schermo che non esiste ancora.
	terreno testimone "$TELA" || { ko "⛔ IL BANCO: il testimone non si apre"; return 3; }
	# ⛔⛔ IL RISCALDAMENTO, e non e' prudenza: e' un difetto del banco misurato
	#     il 21 agosto 2026 e che mi ha dato un rosso falso al primo giro.
	#
	#     `[M]` Il PRIMISSIMO `punta` su una finestra appena aperta produce il
	#     `wl_pointer.enter`, e il clic mandato 0,4 s dopo **non arriva** —
	#     mentre lo stesso identico clic, ripetuto a mano un minuto dopo, arriva.
	#     ⇒ Non e' il difetto di §7.1: e' la finestra che si sta ancora
	#     insediando, e un banco che partisse subito accuserebbe il prodotto di
	#     una cosa che non ha fatto (`CODER.md` §3.10).
	#
	# ⇒ Si scalda PRIMA di `segna`, cosi' le righe dell'insediamento restano
	#   **fuori** dalla finestra di misura invece di doverle scartare dopo.
	di "punta $((TL / 2)) $((TA / 2))"; sleep 1.5
	di "punta $((TL / 3)) $((TA / 3))"; sleep 1.0
	return 0
}

# quante righe ha visto il testimone finora — e' il `--da` del giudice
segna() { terreno righe | awk '{print $2}'; }

giudica() { # $1 etichetta · $2 scena(modo) · $3 da · $4 descrizione
	sudo_mio python3 "$G" --visto "$LAV/visto.jsonl" \
		--iniettore "$LAV/06-b33-risveglio.log" --da "$3" \
		--modo "$2" --etichetta "$1" --tela "$TELA" --esiti "$ESITI" \
		--scena "$4"
	[ $? -eq 0 ] || ESITO=1
}

case "$COSA" in
strumento)
	log "S0 · IL CONTROLLO ZERO — lo strumento sa vedere un clic?"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))"; sleep 0.4
	di "pulsante 272 1";                sleep 0.4
	di "pulsante 272 0";                sleep 0.6
	di "stato";                         sleep 0.3
	giudica s0-strumento strumento "$DA" \
		"clic senza nessun ricambio, testimone aperto prima"
	carico
	exit $ESITO ;;

libero)
	log "S1 · TRE RISVEGLI A MANO ALZATA — §7.1 dice 3 ricambi, e zero ADATTA_TELA"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "stato";     sleep 0.3
	di "risveglia"; sleep 1.2
	di "risveglia"; sleep 1.2
	di "risveglia"; sleep 1.2
	di "stato";     sleep 0.3
	giudica s1-libero libero "$DA" \
		"tre cattura_risveglia() su scena ferma, niente premuto"
	carico
	exit $ESITO ;;

tenuto)
	log "S2 · ⛔ IL PULSANTE TENUTO GIU' MENTRE LA CATTURA SI RISVEGLIA"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "stato";                          sleep 0.3
	# ⛔ UN SOLO risveglio: due renderebbero impossibile dire quale ha fatto il
	#    danno, e il danno e' irreversibile — non si somma, si consuma.
	di "risveglia";                      sleep 1.5
	di "stato";                          sleep 0.3
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	# ⭐ E ADESSO UN CLIC FRESCO: e' la misura che conta davvero — «il desktop
	#    prende ancora i clic?» — e nel banco di ieri non c'era.
	di "punta $((TL * 3 / 4)) $((TA * 3 / 4))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.6
	# ⚠ E un tasto, come controllo INTERNO alla scena: la tastiera non e' un
	#   dispositivo di viewport e non ricambia, quindi DEVE arrivare.  Se non
	#   arrivasse, la causa sarebbe un'altra e il rosso accuserebbe la cosa
	#   sbagliata.
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	di "stato";                          sleep 0.3
	giudica s2-tenuto tenuto "$DA" \
		"BTN_LEFT e Ctrl tenuti giu' durante UN cattura_risveglia(), scena ferma"
	carico
	exit $ESITO ;;

confronto)
	log "S3 · LA PORTA GIA' NOTA — la stessa scena con un RIDIMENSIONAMENTO"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "stato";                          sleep 0.3
	di "ridimensiona ${TELA2%x*} ${TELA2#*x}"; sleep 1.5
	di "ritela ${TELA2%x*} ${TELA2#*x}"; sleep 0.4
	di "stato";                          sleep 0.3
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	di "punta $(( ${TELA2%x*} * 3 / 4 )) $(( ${TELA2#*x} * 3 / 4 ))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.6
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	di "stato";                          sleep 0.3
	giudica s3-confronto tenuto "$DA" \
		"BTN_LEFT e Ctrl tenuti giu' durante un cattura_ridimensiona() (§4.6)"
	carico
	exit $ESITO ;;

guarigione)
	# ⭐⭐ SI GUARISCE SENZA RIACCENDERE LA SESSIONE? — la prova della cura «E».
	#
	# §4.6 dice *«si guarisce solo riaccendendo il server»*.  ⛔ Ma «il server»
	# e' molto piu' di quel che serve: `[R]` l'unico posto in cui Mutter
	# rilascia quel che era premuto e' `drop_device()`, chiamata da
	# `meta_eis_client_disconnect()` (`meta-eis-client.c:1075`) — cioe' dalla
	# **caduta del canale EIS**, che non ha niente a che vedere col processo.
	#
	# ⇒ Qui si rompe il desktop e poi si stacca **soltanto il cliente EIS**,
	#   lasciando in piedi gnome-shell, il monitor e la sessione dell'utente.
	#   Se il clic torna, la cura di recupero esiste e costa un riattacco.
	#
	# ⛔⛔ E IL LIMITE VA DETTO: qui il cliente si spegne INTERO, quindi cade
	#      anche la sessione `RemoteDesktop` e il flusso PipeWire.  ⇒ Questa
	#      misura prova che **un cliente EIS nuovo guarisce il posto**; NON
	#      prova ancora che basti riaprire il **solo** `ConnectToEIS` tenendo su
	#      il palco.  Quella e' `[R]` (`meta-remote-desktop-session.c:1943-1969`:
	#      `session->eis` si riusa e ogni chiamata aggiunge un cliente) e per
	#      renderla `[M]` serve una riga in `mutter.c` che chiuda il descrittore
	#      messo da parte e richiami `ConnectToEIS` — ⚠ senza chiudere quello,
	#      il socket resta aperto e Mutter **non vede nessun distacco**.
	log "S4 · ⭐ SI GUARISCE SENZA TOCCARE LA SESSIONE?"
	carico
	rimonta || exit 3
	DA=$(segna)
	di "punta $((TL / 2)) $((TA / 2))";  sleep 0.4
	di "pulsante 272 1";                 sleep 0.6
	di "posizione 29 1";                 sleep 0.6
	di "risveglia";                      sleep 1.5
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 29 0";                 sleep 0.8
	di "punta $((TL * 3 / 4)) $((TA * 3 / 4))"; sleep 0.4
	di "pulsante 272 1";                 sleep 0.4
	di "pulsante 272 0";                 sleep 0.8
	di "posizione 28 1";                 sleep 0.3
	di "posizione 28 0";                 sleep 0.6
	giudica s4-rotto tenuto "$DA" "il danno, rifatto apposta per poi guarirlo"

	log "E adesso stacco SOLO il cliente EIS — gnome-shell NON si tocca"
	PRIMA_SHELL=$(sudo_mio pgrep -u 1006 -x gnome-shell | head -1)
	terreno iniettore-spegni > /dev/null
	sleep 2
	terreno iniettore-accendi "$TELA" > /dev/null || { ko "⛔ non si riaccende"; exit 3; }
	terreno testimone "$TELA" > /dev/null || { ko "⛔ IL BANCO: testimone"; exit 3; }
	di "punta $((TL / 2)) $((TA / 2))"; sleep 1.5
	di "punta $((TL / 3)) $((TA / 3))"; sleep 1.0
	DOPO_SHELL=$(sudo_mio pgrep -u 1006 -x gnome-shell | head -1)
	# ⛔ E si CONTROLLA che la sessione sia la stessa: se gnome-shell fosse
	#    ripartito, il conto del posto (`MetaSeatImpl`) sarebbe nuovo di zecca e
	#    il verde direbbe soltanto «ho riavviato tutto».
	if [ -n "$PRIMA_SHELL" ] && [ "$PRIMA_SHELL" = "$DOPO_SHELL" ]; then
		ok "gnome-shell e' lo STESSO processo ($PRIMA_SHELL): il posto non e' nuovo"
	else
		ko "⛔ gnome-shell e' cambiato ($PRIMA_SHELL → $DOPO_SHELL): il verde che segue non vale"
	fi
	DA=$(segna)
	di "pulsante 272 1"; sleep 0.4
	di "pulsante 272 0"; sleep 0.8
	giudica s4-guarito strumento "$DA" \
		"lo stesso desktop, dopo il riattacco del solo cliente EIS"
	carico
	exit $ESITO ;;

spegni)
	terreno iniettore-spegni
	terreno testimone-via
	exit 0 ;;

tutto)
	# ⛔⛔ GLI ESITI DEI SOTTO-GIRI SI SOMMANO, e non e' pignoleria: `06-b33-lancia.sh`
	#      aveva qui un `exit 0` e usciva verde con tutti i casi rossi (rilievo
	#      della revisione avversariale, 21 agosto 2026).  Non si ripaga.
	for g in strumento libero tenuto confronto guarigione; do
		bash "$0" "$PAROLA_SUDO" "$g" || ESITO=1
	done
	bash "$0" "$PAROLA_SUDO" spegni > /dev/null
	if [ "$ESITO" -eq 0 ]; then
		ok "⭐ tutte le scene hanno dato quel che l'atteso dichiarava"
	else
		ko "⛔ almeno una scena non e' verde: guarda i sotto-giri qui sopra"
	fi
	exit $ESITO ;;

*)
	echo "⛔ non so fare «$COSA»"; exit 2 ;;
esac
