#!/bin/bash
#
# 06-b33-certifica.sh — ⛔⛔ IL CONTROLLO POSITIVO DEL BANCO `06-b33`.
#
#   ⚠ GIRA SUL SERVER (192.168.0.2), come utente `nicfio`, NON da root e NON
#     dentro il contenitore: e' lui che chiama tutte e due le cose.
#
#   bash 06-b33-certifica.sh /media/REMOTIX/tmp/06-i/sudo-parola [G1 G2 ...]
#
# ⛔ La parola di `sudo` sta in un file `0600` e NON passa mai dalla riga di
#    comando (difetto D12).  ⚠ Quel file lo scrive e lo cancella CHI CHIAMA:
#    questo script non lo crea, cosi' non puo' nemmeno dimenticarsi di
#    cancellarlo.
#
# ===========================================================================
# ⛔ CHE COSA CERTIFICA, E PERCHE' NON BASTA «DIVENTA ROSSO QUALCOSA»
# ===========================================================================
#
# Per ogni guasto innestato in una COPIA di `input.c` si pretende che diventi
# rosso **il caso dichiarato in `06-b33-guasti.py`**, e non un caso qualunque:
# `CODER.md` §3.4 e §3.10.  ⭐ `04-b31-certifica.sh` ha pagato due volte questa
# distinzione il 15 agosto 2026 (l'atteso di G1, e G9 mascherato da un secondo
# controllo), e qui non si ripaga.
#
# ===========================================================================
# ⛔⛔ IL LIMITE DI QUESTO BANCO, SCRITTO IN TESTA PERCHE' NESSUNO CI CADA
# ===========================================================================
#
#   1. ⛔ **NON C'E' NESSUN BROWSER E NESSUN Xvfb.**  Il testimone e' una
#      finestra Wayland nativa, il cliente e' un QUIC nativo.  ⇒ `LEZIONI.md`
#      §1.15 (*su Xvfb `requestAnimationFrame` non gira mai, e in Blink
#      l'evento `resize` si consegna dentro il giro di rendering*) **non tocca**
#      niente di quel che si misura qui — ⛔ e per la stessa ragione questo
#      banco **non puo' dire niente** sulla scala di disegno del client, su
#      `pixelated`, ne' sul cammino della pagina che insegue la finestra.
#      Quelli vivono nel browser e sono della sottofase 6.5.
#   2. ⛔ **Il palco si giudica PRIMA del prodotto**: se il testimone non ha
#      visto nemmeno una riga, o se non c'e' stato nessun `RITELA`, il giudice
#      dice «IL BANCO, NON IL PRODOTTO» e il caso e' rosso per colpa della
#      scena.  Senza quella distinzione un banco senza scena resta verde.
#   3. ⚠ **Una sola sessione grafica per utente** (`SPECIFICHE.md` §5.1): i
#      guasti si provano **in sequenza** sullo stesso utente, spegnendo e
#      riaccendendo il server.  ⭐ E il riavvio serve anche a un'altra cosa: e'
#      l'unica cosa che sblocca il conto dei pulsanti del posto quando un giro
#      «tenuto» l'ha lasciato giu' (`meta-seat-impl.c:899-908`).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?serve il file 0600 con la parola di sudo}
shift
GUASTI=${*:-G1 G2 G3 G4 G5}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
DENTRO=${DENTRO:-/srv/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
LAV_D=${LAV_D:-/srv/remotix/tmp/06-i}
T=$SRC/banchi/06-b33-terreno.sh
ESITI=$LAV/06-b33-certifica.jsonl
SANO=$LAV/input-sano.c
TELA_A=${TELA_A:-1264x800}
TELA_B=${TELA_B:-1000x640}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { ko "⛔ $PAROLA_SUDO non si legge"; exit 2; }

# ⛔ Ogni chiamata rilegge il file: tenere la parola in una variabile di shell la
#    metterebbe in `/proc/<pid>/environ`, che e' la stessa esposizione di D12.
sudo_mio()  { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
dentro()    { printf '%s\n' "$(cat "$PAROLA_SUDO")" | bash /media/REMOTIX/enter.sh "$@"; }

cliente() { # $1 = etichetta · $2 = modo|attacco
	if [ "$2" = attacco ]; then
		dentro "cd $DENTRO/banchi && python3 06-b33-cliente.py --porta 7781 \
			--parola-file $LAV_D/parola --lavoro $LAV_D --tela-a $TELA_A \
			--tela-b $TELA_B --etichetta $1 --solo attacco --prima 6 \
			--scena 'nascita del palco alla tela A'"
	else
		dentro "cd $DENTRO/banchi && python3 06-b33-cliente.py --porta 7781 \
			--parola-file $LAV_D/parola --lavoro $LAV_D --tela-a $TELA_A \
			--tela-b $TELA_B --etichetta $1 --modo $2 --prima 5 --pausa 3 \
			--dopo 5 --scena 'certifica $1, modo $2'"
	fi
}

# ⛔ La scena si rimonta da capo a ogni giro, e il testimone si RIAPRE: il suo
#    contatore riparte da 1, e il giudice legge «da 5» (le righe di apertura).
#    ⚠ Senza, il giudice del giro N vedrebbe le righe del giro N-1 e darebbe
#      verde a un prodotto guasto.
giro() { # $1 = etichetta · $2 = modo
	sudo_mio bash "$T" spegni  > /dev/null 2>&1
	sleep 2
	sudo_mio bash "$T" accendi > /dev/null 2>&1 || { ko "il server non si accende"; return 3; }
	cliente "$1-nasc" attacco  > /dev/null 2>&1
	sudo_mio bash "$T" testimone "$TELA_A" > /dev/null 2>&1 || {
		ko "⛔ IL BANCO: il testimone non si apre"; return 3; }
	cliente "$1" "$2" > "$LAV/$1-cliente.log" 2>&1
	sudo_mio python3 "$SRC/banchi/06-b33-giudice.py" --visto "$LAV/visto.jsonl" \
		--registro "$LAV/registro.log" --da 5 --modo "$2" --etichetta "$1" \
		--tela-b "$TELA_B" --scena "certifica $1" --esiti "$ESITI"
	return 0
}

# ⛔ Il caso che il giudice ha acceso, letto dagli ESITI e non dedotto
#    dall'uscita a schermo.
rossi() { python3 - "$ESITI" "$1" <<'EOF'
import json, sys
righe = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
for r in reversed(righe):
    if r["etichetta"] == sys.argv[2]:
        print(" ".join(c["caso"].split()[0] for c in r["casi"]
                       if c["esito"] == "NO"))
        break
EOF
}

log "0. La copia SANA di input.c, che e' quel che si rimette dopo ogni guasto"
cp "$SRC/src/input.c" "$SANO" || { ko "non ho fatto la copia"; exit 2; }
ok "salvata in $SANO ($(wc -l < "$SANO") righe)"
: > "$ESITI"

log "1. Il giro SANO — ⛔ e se questo non e' verde non si certifica niente"
dentro "bash $DENTRO/src/costruisci.sh" > "$LAV/costr-sano.log" 2>&1
giro sano comanda
R=$(rossi sano)
if [ -z "$R" ]; then
	ok "il giro sano non ha nessun rosso"
else
	ko "⛔ il giro SANO ha dei rossi: $R — il banco non e' certificabile"
	exit 3
fi

for G in $GUASTI; do
	CASO=$(python3 "$QUI/06-b33-guasti.py" --elenco | grep -A1 "^$G " | \
		sed -n 's/.*deve accendere: //p')
	log "2.$G — deve accendere il caso $CASO"
	cp "$SANO" "$SRC/src/input.c"
	python3 "$QUI/06-b33-guasti.py" --file "$SRC/src/input.c" --guasto "$G" || {
		ko "$G non si e' innestato"; continue; }
	# ⛔ E si guarda l'esito del COSTRUTTORE, non la presenza del file: un
	#    binario di ieri risponde «si'» a *esiste?* come uno di adesso.
	if ! dentro "bash $DENTRO/src/costruisci.sh" > "$LAV/costr-$G.log" 2>&1; then
		ko "$G non compila:"; tail -5 "$LAV/costr-$G.log" | sed 's/^/        /'
		continue
	fi
	MODO=comanda
	case "$CASO" in R*) MODO=tenuto ;; esac
	giro "$G" "$MODO"
	R=$(rossi "$G")
	inf "casi rossi: ${R:-nessuno}"
	case " $R " in
	*" $CASO "*) ok "⭐ $G ha acceso il caso dichiarato ($CASO)" ;;
	*) ko "⛔ $G NON ha acceso $CASO — ha acceso «${R:-nulla}».  ⚠ O il guasto "
	   ko "   non e' quello che credo, o il controllo non sa vederlo: si "
	   ko "   corregge l'ATTESO con la ragione scritta accanto, non il verdetto" ;;
	esac
done

log "3. Si rimette il file SANO e si ricostruisce"
cp "$SANO" "$SRC/src/input.c"
dentro "bash $DENTRO/src/costruisci.sh" > "$LAV/costr-risana.log" 2>&1
if grep -q 'costruito' "$LAV/costr-risana.log"; then
	ok "risanato e ricostruito"
else
	ko "⛔ il risanamento NON ha ricostruito: l'albero resta GUASTO"
fi
giro risanato comanda
R=$(rossi risanato)
[ -z "$R" ] && ok "il giro risanato non ha nessun rosso" || ko "⛔ risanato con rossi: $R"

log "Esito"
inf "esiti: $ESITI"
exit $ESITO
