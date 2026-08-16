#!/bin/bash
#
# 05-b2-ciclo-sessione.sh — ⭐ IL CICLO CHE L'UTENTE FACEVA A MANO.
#
#   sudo bash 05-b2-ciclo-sessione.sh [giri] [larghezza] [altezza]
#
# ---------------------------------------------------------------------------
# ⛔⛔ PERCHE' ESISTE, ED E' UNA LEZIONE PRIMA CHE UN BANCO
#
# La mattina del 16 agosto 2026 l'utente ha provato **cinque volte** la stessa
# scena — collegati, esci, ricollegati — e ogni volta trovava un difetto diverso:
# bande nere, desktop «rotto», nessun input, il desktop che compare dopo molti
# secondi.  ⛔ Ogni volta io curavo il sintomo che il registro mostrava, e lo
# rimandavo a provare.  Al quinto giro ha detto: *«basta test, interpellami solo
# quando e' tutto a posto»*.
#
# ⭐ Aveva ragione due volte: perche' era stanco di fare la cavia, e perche' quei
#    quattro sintomi erano **una causa sola** — la tela chiesta all'`ATTACCA` era
#    1920x1080 fissa, quindi ogni sessione nasceva sbagliata e si
#    ridimensionava, e quel ridimensionamento e' una gara che a volte si perde.
#
# ⇒ Questo file e' il banco che avrebbe dovuto esistere PRIMA di chiedergli di
#   provare: fa il giro da solo, quante volte serve, e dichiara l'atteso prima.
#
# ---------------------------------------------------------------------------
# ⛔ L'ATTESO, DICHIARATO PRIMA (regola B0.4 di `LEZIONI.md`) — per ogni giro:
#
#   1. la sessione si apre con la tela CHIESTA (non un'altra);
#   2. ⛔ NESSUN `NON_ORA`: la tela non si rinegozia, perche' nasce giusta;
#   3. ⛔ NESSUN «il palco non e' alla tela in vigore»: niente ballo;
#   4. la regione del puntatore e' quella della tela — o l'input finisce nel
#      posto sbagliato, ed e' il difetto «nessun input» dell'utente;
#   5. arriva almeno un fotogramma della misura giusta.
#
# ⚠ E fra un giro e l'altro si ESCE davvero, con `SessionManager.Logout(1)`:
#   e' la porta del menu, non `pkill` — che ammazzerebbe anche il figlio e
#   misurerebbe il proprio attrezzo (`fasi/05-la-sessione.md`).
set -uo pipefail

GIRI=${1:-3}
L=${2:-2544}
A=${3:-926}
REG=/media/REMOTIX/tmp/04-vero/registro.log
ENTRA=/media/REMOTIX/enter.sh
ESITO=0

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "⛔ vuole root"; exit 2; }

esci_dal_desktop()
{
	runuser -u prova -- env XDG_RUNTIME_DIR=/run/user/1001 \
		DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus \
		gdbus call --session --dest org.gnome.SessionManager \
		  --object-path /org/gnome/SessionManager \
		  --method org.gnome.SessionManager.Logout 1 >/dev/null 2>&1
}

echo "== il ciclo della sessione: $GIRI giri, tela ${L}x${A} =="
echo "   atteso: nessun NON_ORA, nessun ballo della tela, la regione giusta"

for g in $(seq 1 "$GIRI"); do
	echo
	echo "── giro $g ──"
	RIGHE=$(wc -l < "$REG")

	# ⛔ 45 secondi attaccato, e il numero e' una lezione: la prima stesura ne
	#    dava 25, e i tre giri erano rossi.  ⚠ Non per un difetto del prodotto —
	#    dopo un logout la sessione grafica NASCE da zero, e `gnome-session` ci
	#    mette una decina di secondi; con un client impaziente il banco misurava
	#    **la propria fretta** e la chiamava difetto.  ⭐ E' la forma «una prova
	#    rossa su codice giusto», che costa quanto quella verde su codice rotto.
	bash "$ENTRA" --root "cd /srv/src/04-vero-src/banchi && timeout 120 python3 \
	    01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7700 --utente prova \
	    --parola prova2026 --larghezza $L --altezza $A --resta 70" \
	    >/tmp/05-b2-cli-$g.log 2>&1

	NUOVE=$(tail -n +$((RIGHE + 1)) "$REG")

	# 1. la sessione si apre con la tela chiesta
	if echo "$NUOVE" | grep -aq "sessione aperta utente=prova.*tela=${L}x${A}"; then
		ok "la sessione si apre con la tela chiesta (${L}x${A})"
	else
		ko "la sessione NON si apre con ${L}x${A}: $(echo "$NUOVE" | grep -a 'sessione aperta' | tail -1 | grep -o 'tela=[0-9x]*')"
	fi

	# 2. nessun NON_ORA
	if echo "$NUOVE" | grep -aq "NON_ORA"; then
		ko "c'e' stato un NON_ORA: la tela si e' dovuta rinegoziare"
		echo "$NUOVE" | grep -a "NON_ORA" | head -2 | sed 's/^/        /' | cut -c1-120
	else
		ok "nessun NON_ORA"
	fi

	# 3. nessun ballo
	if echo "$NUOVE" | grep -aq "non e' alla tela in vigore"; then
		ko "il palco e la tela in vigore hanno litigato (il ballo)"
	else
		ok "nessun ballo fra palco e tela"
	fi

	# 4. la regione del puntatore
	R=$(echo "$NUOVE" | grep -a "regione del puntatore per chiave" | tail -1 | grep -o "0,0 [0-9]*x[0-9]*")
	if [ "$R" = "0,0 ${L}x${A}" ]; then
		ok "la regione del puntatore e' ${L}x${A}"
	else
		ko "la regione del puntatore e' «$R» invece di «0,0 ${L}x${A}» ⇒ l'input finirebbe nel posto sbagliato"
	fi

	# 5. almeno un fotogramma della misura giusta
	N=$(echo "$NUOVE" | grep -ac "SPEDITO.*${L}x${A}")
	if [ "$N" -gt 0 ]; then
		ok "$N fotogrammi spediti a ${L}x${A}"
	else
		ko "nessun fotogramma spedito a ${L}x${A}"
	fi

	inf "esco dal desktop (SessionManager.Logout, come la voce del menu)"
	esci_dal_desktop
	# ⛔ SI ASPETTA IL FATTO, NON L'OROLOGIO — e la prima stesura dormiva sei
	#    secondi fissi.  ⚠ La sessione vecchia ci mette di piu' a morire, e il
	#    giro dopo si attaccava MENTRE quella stava chiudendo: due giri rossi su
	#    tre, e il difetto era del banco.
	# ⭐ E' la stessa regola che il progetto paga da sempre: un banco che dorme
	#    misura il proprio sonno (`LEZIONI.md` §2.3-quinquies, i tredici secondi
	#    degli appunti di KDE).
	for i in $(seq 1 30); do
		pgrep -u prova gnome-shell >/dev/null 2>&1 || break
		sleep 1
	done
	if pgrep -u prova gnome-shell >/dev/null 2>&1; then
		ko "la sessione grafica non e' morta entro 30 s dal logout"
	else
		inf "la sessione vecchia e' finita: il giro dopo parte pulito"
	fi
	sleep 2
done

echo
if [ "$ESITO" -eq 0 ]; then
	echo "⭐ $GIRI giri, tutti puliti: la sessione nasce, si esce e si rientra senza ballo."
else
	echo "⛔ almeno un giro ha un rosso: leggi sopra."
fi
exit "$ESITO"
