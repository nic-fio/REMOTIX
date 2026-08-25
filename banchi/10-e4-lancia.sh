#!/usr/bin/env bash
# ===========================================================================
# 10-e4-lancia — ⭐ GLI UNDICI DESKTOP VERI, RIFATTI SULL'ALBERO CUCITO
#
#   E' il lanciatore dell'incarico E4 del quinto giro della fase 10: rifa' le
#   tre scene di `fasi/10-…md` §6.12 (`satura`, `vero`, `ferma`) sull'albero che
#   porta le QUATTRO cure cucite insieme (C1 guardiano · C2 ripiego · C3
#   undicesimo · C4 registro), e le confronta con i numeri del quarto giro.
#
#   ⛔ NON riscrive `10-b92-dieci.py`: gli passa il PROPRIO ambiente e lo
#      chiama, che e' la regola di `09-b86` e di tutta la fase.
#
#   isolamento: porta 8330 · albero /media/REMOTIX/src/10e4-src ·
#               lavoro /media/REMOTIX/tmp/10e4 · unita' remotix-8330 ·
#               utenti provamt1…provamt11 (⛔ CONDIVISI: lucchetto prima)
#
# ⛔⛔ IL LUCCHETTO SI PRENDE E SI MOLLA **A OGNI SCENA**, non per campagna.
#
#   ⚠ La prima stesura ne dichiarava uno solo da 12 600 s per tutt'e tre le
#     scene, e il ragionamento non era sbagliato — `[M]` §7.3: una coda puo'
#     durare 98 minuti, e tre code sono peggio di una.  ⛔ Ma dietro c'erano tre
#     incarichi fermi, e le tre scene sono **giri indipendenti**: ognuna apre le
#     sue sessioni, misura i suoi gradini e sgombera.
#   ⇒ ⭐ Prendere e mollare a ogni scena non toglie NIENTE alla misura, perche'
#     ogni giro rifa' il controllo del terreno e verifica i palchi orfani prima
#     di partire — e restituisce agli altri un turno in mezzo.
#   ⛔ Quel che NON si puo' fare e' spezzare una scena a meta': un gradino
#     interrotto non vale, e l'ancora della satura (⭐ deve ritrovare il SEI) ha
#     senso solo se quella scena e' girata intera.
#
#   Il lucchetto lo tiene il lanciatore (`LUCCHETTO_ESTERNO=1`), e
#   `10-b0-terreno.sh` lo verifica con `LUCCHETTO_MIO=1` — cioe' pretende che
#   sia MIO, non che sia libero.
#
# ⛔ E LA SCADENZA SI DICHIARA COL MARGINE (§7.3, sesta trappola): una scadenza
#    sottostimata regala la GPU a meta' misura, e da quel momento due carichi si
#    falsano in silenzio — chi la prende misura su undici palchi vivi credendo
#    la macchina sgombra.
#
# uso:
#   bash banchi/10-e4-lancia.sh porta        # spedisce e compila l'albero cucito
#   bash banchi/10-e4-lancia.sh utenti       # ⛔ NON rifa' le parole d'ordine
#   bash banchi/10-e4-lancia.sh accendi|spegni|stato|sgombra|sblocca
#   bash banchi/10-e4-lancia.sh certifica    # ⛔ non tocca la macchina di prova
#   bash banchi/10-e4-lancia.sh prendi       # la corsa al lucchetto, SULLA macchina
#   bash banchi/10-e4-lancia.sh molla
#   bash banchi/10-e4-lancia.sh scena satura|vero|ferma   # ⛔ col lucchetto gia' in mano
# ===========================================================================
set -uo pipefail

QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8330}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10e4-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10e4}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10e4-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10e4}
export UNITA=${UNITA:-remotix-$PORTA}
export QUANTI=${QUANTI:-10}          # +1 = l'undicesimo, che sta a parte
export CON_UNDICESIMO=1
export IO_SONO=${IO_SONO:-10-e4}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export FUORI=${FUORI:-/tmp/10-e4}
# ⛔ `/dev/shm` e' UNO per macchina: il contatore dei disegni deve portare un
#    nome mio, o due banchi si leggerebbero il contatore a vicenda.
export SHM_BASE=${SHM_BASE:-10e4}
export PAROLA_UTENTE=${PAROLA_UTENTE:-mt-dieci-2026}
# ⛔ Le porte che NON sono mie: si contano, non si toccano.  La 8100 e' quella
#    del quarto giro, e va nell'elenco proprio perche' NON e' mia.
export VICINE=${VICINE:-"7700 7730 7900 7910 7920 8000 8010 8020 8030 8040 8050 8060 8070 8080 8090 8100"}

# ⭐ Il possesso di UNA scena, dichiarato col margine — e le parti vere sono
#    misurate, non stimate: `[M]` 25 agosto 2026, la scena `satura` di questo
#    incarico e' durata **12 minuti** in tutto (terreno 21 predicati + 11
#    gradini da 45 s a regime + sgombero).
#    ⛔ Il margine e' quello di §7.3 (63 minuti stimati → 101 dichiarati, ×1,6),
#    e qui si allarga a ×3 perche' `[M]` l'apertura dell'ennesima sessione «sotto
#    carico non e' un secondo: da 2 a 40 s».  ⇒ 2 400 s (40 min) per una scena.
#    ⚠ Sbagliare in BASSO costa la misura a tutt'e due: chi arriva dopo la
#      scadenza scassina e misura su undici palchi vivi credendo la macchina
#      sgombra.
POSSESSO=${POSSESSO:-2400}
ATTESA=${ATTESA:-21600}

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

PASSO=${1:-stato}
case "$PASSO" in
porta|utenti|accendi|spegni|sblocca|stato|sgombra|uno-per-volta)
	exec bash "$QUI/banchi/10-b91-terreno-dieci.sh" "$PASSO" ;;

certifica)
	# ⛔ Non tocca la macchina di prova: e' il controllo positivo del banco.
	exec python3 "$QUI/banchi/10-b92-dieci.py" --certifica ;;

prendi)
	# ⛔⛔ LA CORSA SI CORRE SULLA MACCHINA, non da qui: `09-lucchetto.py`
	#     ritenta ogni 5 s, e `[M]` §7.3 dice che con 5 s si perdono cinque
	#     passaggi di mano di fila.  ⭐ `10-b9d-corri-al-lucchetto.sh` ritenta
	#     ogni 0,5 s dalla macchina stessa: `[M]` 47 ms dopo il rilascio.
	scp -q -o BatchMode=yes "$QUI/banchi/10-b9d-corri-al-lucchetto.sh" \
		"$MACCHINA:/tmp/10-e4-corri.sh" || { ko "non ho spedito il corridore"; exit 2; }
	log "La corsa al lucchetto — «$IO_SONO», possesso $POSSESSO s, attesa $ATTESA s"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /tmp/10-e4-corri.sh \
		 '$LUCCHETTO' '$IO_SONO' $POSSESSO $ATTESA 0.5"
	exit $? ;;

molla)
	# ⛔ NON «scassina»: quello fa `rm -rf` senza guardare di chi e'.  ⭐ `molla()`
	#    verifica che il lucchetto porti ancora il MIO nome e si rifiuta se nel
	#    frattempo mi hanno scassinato — che e' l'unico modo di non togliere la
	#    GPU a chi ha appena cominciato a misurare.
	exec env LUCCHETTO="$LUCCHETTO" python3 -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('luc', '$QUI/banchi/09-lucchetto.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sys.exit(0 if m.molla('$IO_SONO') else 1)
" ;;

scena)
	S=${2:?serve satura|vero|ferma}
	D=${3:-45}
	# ⛔ Il lucchetto e' GIA' MIO e lo tiene questo lanciatore: il banco non lo
	#    prende e non lo molla, e il terreno lo verifica con LUCCHETTO_MIO=1.
	export LUCCHETTO_ESTERNO=1
	export FUORI="$FUORI/$S"
	mkdir -p "$FUORI"
	log "SCENA «$S» — 11 gradini da $D s a regime, albero cucito ($ALBERO)"
	python3 "$QUI/banchi/10-b92-dieci.py" salita --scena "$S" --quanti 11 --durata "$D"
	exit $? ;;
*)
	ko "passo sconosciuto: $PASSO"
	sed -n '/^# uso:/,/^# ===/p' "$0"
	exit 2 ;;
esac
