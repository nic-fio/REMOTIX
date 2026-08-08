#!/bin/bash
#
# Fase 11, voce 4: gli appunti su KDE.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase11-appunti.sh
#
# Va eseguita SUL SERVER: mette insieme la sessione Plasma — che gira qui — e il
# contenitore di sviluppo, dove c'e' il client di prova.  Prova i due versi, con
# accenti, e mette alla prova la guardia contro l'eco.
#
# ⛔ I DUE LATI SI PARLANO CON MARCATORI, NON CON LE ATTESE A TEMPO.  Al primo
#    giro erano sincronizzati a `sleep`: i due orologi partivano sfasati di
#    tredici secondi e il banco ha BOCCIATO UN CODICE CHE FUNZIONAVA — la
#    sessione incollava la propria copia, arrivata dopo quella del client.
#    (`LEZIONI.md` §2.3)
#
# ⚠ Chi mette qualcosa negli appunti RESTA IN VITA a tenerli (`wl-copy`,
#   `xclip`): va mandato in fondo e staccato alla fine.  E su `enter.sh` non si
#   dirotta MAI l'uscita, perche' dentro c'e' un `sudo` che chiede la parola
#   d'ordine proprio li'.
set -u

BASE=/media/REMOTIX
BIN="$BASE/src/remotix-c/build/src/remotix"
PORTA=3399
FUORI=/media/REMOTIX/tmp        # come lo vede la macchina
DENTRO=/srv/remotix/tmp         # come lo vede il contenitore
R=/run/user/$(id -u)/remotix-appunti.log
DAL_SERVER="SESSIONE-VERSO-CLIENT-àèìòù-ok"
DAL_CLIENT="CLIENT-VERSO-SESSIONE-àèìòù-ok"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
#
# GUASTI VIAGGIA SU FILE, e non e' un vezzo: il lato sessione gira in un
# sottoprocesso (`lato_sessione &`), e una variabile incrementata li' dentro NON
# torna al padre.  Contando in memoria questo banco ha stampato «guasti: 0»
# sotto a un controllo rosso, e sarebbe uscito con stato ZERO: un banco che
# mente a chi lo automatizza e' peggio di un banco che manca.
CONTO=$(mktemp); echo 0 > "$CONTO"
ko()  { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; echo $(( $(cat "$CONTO") + 1 )) > "$CONTO"; }
GUASTI=0
attendi() { for _ in $(seq 60); do [ -e "$FUORI/$1" ] && return 0; sleep 1; done; return 1; }

[ -x "$BIN" ] || { echo "manca $BIN: costruiscilo prima"; exit 1; }
mkdir -p "$FUORI"
rm -f "$FUORI"/app-*.txt "$FUORI"/app-*.marca "$FUORI"/app-*.err

# --- il lato client, che gira nel contenitore ------------------------------
cat > "$FUORI/app-client.sh" <<'CLIENT'
set -u
D=:77
FUORI=/srv/remotix/tmp
attendi() { for _ in $(seq 60); do [ -e "$FUORI/$1" ] && return 0; sleep 1; done; return 1; }
pkill -f "^Xvfb $D" 2>/dev/null
Xvfb $D -screen 0 1280x1024x24 >/dev/null 2>&1 &
sleep 2
# La clipboard del client si SVUOTA: quel che resta dal giro prima verrebbe
# annunciato alla connessione e si scambierebbe per un risultato.
DISPLAY=$D xclip -i -selection clipboard < /dev/null
DISPLAY=$D timeout 120 xfreerdp3 /v:127.0.0.1:PORTA_QUI /size:1024x768 /gfx:AVC420 \
	/cert:ignore /sec:tls /u:prova /p:prova +clipboard /log-level:WARN \
	>$FUORI/app-client.log 2>&1 &
RDP=$!
sleep 6
touch $FUORI/app-collegato.marca
attendi app-sessione-ha-copiato.marca
sleep 3
DISPLAY=$D xclip -o -selection clipboard > $FUORI/app-verso-client.txt 2>$FUORI/app-verso-client.err
touch $FUORI/app-client-ha-letto.marca
printf 'TESTO_QUI' | DISPLAY=$D xclip -i -selection clipboard &
sleep 3
touch $FUORI/app-client-ha-copiato.marca
attendi app-finito.marca
kill $RDP 2>/dev/null; wait $RDP 2>/dev/null
pkill -f "^xclip" 2>/dev/null
pkill -f "^Xvfb $D" 2>/dev/null
true
CLIENT
sed -i "s/PORTA_QUI/$PORTA/; s/TESTO_QUI/$DAL_CLIENT/" "$FUORI/app-client.sh"

# --- il lato sessione, che gira qui ----------------------------------------
lato_sessione()
{
	export WAYLAND_DISPLAY=$(cd "$XDG_RUNTIME_DIR" && ls -1 wayland-[0-9] 2>/dev/null | head -1)
	attendi app-collegato.marca || { ko "il client non si e' collegato"; return; }

	printf '%s' "$DAL_SERVER" | wl-copy &
	sleep 2
	touch "$FUORI/app-sessione-ha-copiato.marca"

	titolo "1. la sessione copia, e REMOTIX se ne accorge"
	sleep 2
	grep -aq 'la sessione ha copiato qualcosa' "$R" \
		&& ok "$(grep -a 'la sessione ha copiato qualcosa' "$R" | tail -1 | sed 's/.*INFO *//')" \
		|| ko "nessun annuncio nel registro"

	titolo "2. …e il client lo riceve, accenti compresi"
	attendi app-client-ha-letto.marca || ko "il client non ha letto"
	letto=$(cat "$FUORI/app-verso-client.txt" 2>/dev/null || true)
	[ "$letto" = "$DAL_SERVER" ] && ok "il client ha «$letto»" \
		|| ko "il client ha «$letto» invece di «$DAL_SERVER»"

	titolo "3. il client copia, e la sessione lo incolla"
	attendi app-client-ha-copiato.marca || ko "il client non ha copiato"
	sleep 2
	pkill -f '^wl-copy' 2>/dev/null   # chi teneva la nostra copia lascia il campo
	if timeout 8 wl-paste --no-newline > "$FUORI/app-dalla-sessione.txt" 2>/dev/null; then
		letto=$(cat "$FUORI/app-dalla-sessione.txt")
		[ "$letto" = "$DAL_CLIENT" ] && ok "la sessione incolla «$letto»" \
			|| ko "la sessione incolla «$letto» invece di «$DAL_CLIENT»"
	else
		ko "wl-paste non ha ottenuto niente"
	fi

	titolo "4. l'eco di KWin, riconosciuta e non inseguita"
	annunci=$(grep -ac 'la sessione ha copiato qualcosa' "$R" || true)
	echi=$(grep -ac 'annuncio di ritorno' "$R" || true)
	printf '    --    annunci veri: %s   echi buttati: %s\n' "$annunci" "$echi"
	[ "$annunci" -le 3 ] && ok "nessun ciclo" || ko "troppi annunci ($annunci): i due lati si rincorrono"
	# ⛔ Che l'eco ARRIVI e' parte della prova: se non arrivasse, la guardia non
	#    sarebbe stata messa alla prova e il verde non direbbe niente.
	[ "$echi" -ge 1 ] && ok "l'eco e' arrivata ed e' stata riconosciuta" \
		|| ko "nessuna eco: la guardia non e' stata provata"

	touch "$FUORI/app-finito.marca"
}

titolo "REMOTIX in ascolto sulla $PORTA"
pkill -x remotix 2>/dev/null; pkill -f '^wl-copy' 2>/dev/null; sleep 1
setsid nohup "$BIN" --compositore kwin --senza-autenticazione --porta "$PORTA" \
	--registro diagnostica > "$R" 2>&1 &
sleep 2
[ "$(ss -ltn | grep -c ":$PORTA")" = 1 ] && ok "porta aperta" || ko "porta chiusa"

lato_sessione &
LATO=$!
bash "$BASE/enter.sh" "bash $DENTRO/app-client.sh"
wait $LATO

titolo "il registro degli appunti"
grep -aE 'appunti:|sessione ha copiato|annuncio di ritorno' "$R" | tail -10 | sed 's/^/    /'
pkill -x remotix 2>/dev/null; pkill -f '^wl-copy' 2>/dev/null
GUASTI=$(cat "$CONTO"); rm -f "$CONTO"
titolo "guasti: $GUASTI"
exit $((GUASTI > 0))
