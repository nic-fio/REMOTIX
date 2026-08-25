#!/bin/bash
#
# 05-b4-riattacco-altra-misura.sh — ⭐ CI SI RIATTACCA DA UNO SCHERMO DIVERSO.
#
#   sudo bash 05-b4-riattacco-altra-misura.sh
#
# ---------------------------------------------------------------------------
# ⛔⭐ PERCHE' ESISTE, ED E' UNA PROVA DI NON-REGRESSIONE PRIMA CHE UNA PROVA
#
# Il 16 agosto 2026 la cura della coda dei tempi di login ha aggiunto una
# guardia: *il figlio non fa nascere la sessione ne' monta il palco finche' non
# sa la tela del cliente*.  ⭐ Ha tolto diciassette secondi di coda.
#
# ⚠ Ma tocca ESATTAMENTE il percorso del ridimensionamento, e quel percorso ha
#   un secondo caso che la misura dei venti giri NON copre: la sessione e' gia'
#   viva, il cliente se ne va, e ne torna uno con uno schermo di un'altra
#   misura.  ⛔ Li' la guardia non deve bloccare niente (la tela «dal cliente»
#   c'e' gia'), e il palco deve ridimensionarsi.
#
# ⇒ E' anche il caso VERO dell'utente: si stacca dal portatile e si riattacca
#   dal telefono.  `FASI.md` §05-la-sessione lo tiene fra i punti aperti.
#
# ---------------------------------------------------------------------------
# ⛔⛔ E LA PRIMA STESURA DI QUESTO BANCO AVEVA L'ATTESO SBAGLIATO — 16 agosto
#     2026, ed e' la QUARTA volta in un giorno che un banco misura se stesso.
#
# Pretendeva che il secondo cliente vedesse fotogrammi alla PROPRIA misura, e
# dava rosso.  ⭐ Ma il prodotto fa una cosa diversa **e dichiarata**, e il
# registro la scriveva:
#
#   «⚠ RIPIEGO DICHIARATO (§4.5): chiesta la tela 1280x720, ma il palco di
#    prova ne ha gia' una — 2544x926 — e sopravvive al client (I4).  CONCESSA
#    quella del palco: cosi' i fotogrammi arrivano DA SUBITO, e la pagina puo'
#    chiedere la sua misura con `ADATTA_TELA`»
#
# ⇒ Al riattacco si concede la tela del PALCO — si passa per uno stato in cui i
#   pixel ARRIVANO invece che per uno in cui non arrivano — ⭐ e il pezzo finale
#   lo fa **la pagina**, con `ADATTA_TELA`.
#
# ⛔⛔ E QUESTO BANCO NON PUO' PROVARLO: `01-b3-cliente.py` non conosce
#     `ADATTA_TELA` (zero occorrenze; la pagina ne ha 45).  ⇒ La misura del
#     riattacco da uno schermo diverso SI FA COL BROWSER, non qui — ed e'
#     esattamente quel che l'utente aveva detto: «per i test usa il browser,
#     non il banco: e' l'unico modo di misurare effettivamente quello che
#     accade».
#
# ---------------------------------------------------------------------------
# ⛔ L'ATTESO, DICHIARATO PRIMA (regola B0.4 di `LEZIONI.md`) — e solo quel che
#    questo banco PUO' vedere:
#
#   1. il primo cliente vede fotogrammi alla SUA misura;
#   2. la sessione grafica SOPRAVVIVE fra i due attacchi (invariante I4);
#   3. ⛔ e NON rinasce: `avvii` dev'essere 0 nel secondo giro, altrimenti
#      stiamo misurando un login nuovo e non un riattacco — e l'utente avrebbe
#      perso i suoi programmi;
#   4. ⭐ al secondo cliente i fotogrammi arrivano SUBITO, alla tela del palco:
#      e' il punto del ripiego di §4.5, «pixel adesso invece di niente»;
#   5. ⏳ che la tela poi diventi quella del secondo schermo si vede col
#      BROWSER, e questo banco lo DICHIARA invece di far finta di provarlo.
set -uo pipefail

L1=${1:-2544}; A1=${2:-926}
L2=${3:-1280}; A2=${4:-720}
REG=/media/REMOTIX/tmp/04-vero/registro.log
ENTRA=/media/REMOTIX/enter.sh
ESITO=0

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "⛔ vuole root"; exit 2; }

attacca()   # <larghezza> <altezza> <quanti secondi restare>
{
	bash "$ENTRA" --root "cd /srv/src/04-vero-src/banchi && timeout 90 python3 \
	    01-b3-cliente.py --indirizzo 192.168.0.2 --porta 7700 --utente prova \
	    --parola prova2026 --larghezza $1 --altezza $2 --resta $3" >/dev/null 2>&1 &
	CLI=$!
	for i in $(seq 1 60); do
		sleep 1
		tail -n +$((RIGHE + 1)) "$REG" 2>/dev/null | grep -aq "SPEDITO.*${1}x${2}" && break
	done
	kill $CLI 2>/dev/null; wait $CLI 2>/dev/null
}

echo "== riattacco da uno schermo diverso: ${L1}x${A1} → ${L2}x${A2} =="
echo

# ── 1. il primo cliente ──────────────────────────────────────────────────
RIGHE=$(wc -l < "$REG")
echo "── primo cliente, ${L1}x${A1} ──"
attacca "$L1" "$A1" 12
NUOVE=$(tail -n +$((RIGHE + 1)) "$REG")
N1=$(echo "$NUOVE" | grep -ac "SPEDITO.*${L1}x${A1}")
[ "$N1" -gt 0 ] && ok "$N1 fotogrammi a ${L1}x${A1}" \
                || ko "nessun fotogramma a ${L1}x${A1}"

# ⛔ Si aspetta che il posto si liberi DAVVERO prima di riattaccare: senza, il
#    secondo cliente troverebbe il posto occupato e il banco misurerebbe la
#    propria fretta (e' la lezione del 16 agosto, tre volte in un giorno).
for i in $(seq 1 40); do
	tail -n +$((RIGHE + 1)) "$REG" | grep -aq "posto LASCIATO da prova" && break
	sleep 1
done
sleep 2

# ── 2. il secondo cliente, misura diversa, sessione ancora viva ──────────
if ! pgrep -u prova gnome-shell >/dev/null 2>&1; then
	ko "⛔ la sessione grafica e' MORTA fra i due attacchi: questo non e' piu' un riattacco"
	echo "   (l'invariante I4 dice che il palco sopravvive al cliente)"
	exit 1
fi
ok "la sessione grafica e' ancora viva fra i due attacchi (I4)"

RIGHE=$(wc -l < "$REG")
echo
echo "── secondo cliente, ${L2}x${A2} (stessa sessione) ──"
attacca "$L2" "$A2" 12
NUOVE=$(tail -n +$((RIGHE + 1)) "$REG")

NTOT=$(echo "$NUOVE" | grep -ac "SPEDITO")
AVVII=$(echo "$NUOVE" | grep -ac "avvio la sessione grafica")
CONC=$(echo "$NUOVE" | grep -a "sessione aperta utente=prova" | tail -1 | grep -o "tela=[0-9]*x[0-9]*")

[ "$NTOT" -gt 0 ] \
	&& ok "$NTOT fotogrammi arrivati SUBITO al secondo cliente (§4.5: pixel adesso invece di niente)" \
	|| ko "nessun fotogramma al secondo cliente: il ripiego di §4.5 non ha funzionato"
[ "$AVVII" -eq 0 ] \
	&& ok "la sessione NON e' rinata: e' un riattacco, non un login nuovo" \
	|| ko "⛔ la sessione e' rinata ($AVVII avvii): l'utente ha perso i suoi programmi"
if [ "$CONC" = "tela=${L1}x${A1}" ]; then
	ok "concessa la tela del palco ($CONC), come §4.5 dichiara per il riattacco"
elif [ "$CONC" = "tela=${L2}x${A2}" ]; then
	ok "⭐ concessa direttamente la tela chiesta ($CONC): meglio del ripiego"
else
	ko "tela concessa inattesa: «$CONC»"
fi

echo
echo "    ⏳ ⛔ QUEL CHE QUESTO BANCO NON PUO' PROVARE, e lo dichiara:"
echo "       che la tela diventi poi ${L2}x${A2} dipende da ADATTA_TELA, che manda"
echo "       LA PAGINA — e 01-b3-cliente.py non lo conosce.  Si misura col"
echo "       BROWSER: staccarsi da una finestra e riattaccarsi da una piu' piccola."

echo
if [ "$ESITO" -eq 0 ]; then
	echo "⭐ il riattacco regge: la sessione RESTA, i pixel arrivano subito."
	echo "   ⏳ che poi la tela diventi quella del secondo schermo lo dice il browser."
else
	echo "⛔ almeno un rosso: leggi sopra."
fi
exit "$ESITO"
