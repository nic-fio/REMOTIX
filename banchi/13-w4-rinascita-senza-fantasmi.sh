#!/bin/bash
# ===========================================================================
# 13-w4 — ⛔⛔ DOPO «ESCI» E UN NUOVO ACCESSO, LO SCHERMO NON LAMPEGGIA
#
#   podman exec rete11-kde bash /opt/remotix/13-w4-rinascita-senza-fantasmi.sh [PORTA]
#
# ⭐⭐ QUESTO BANCO E' DIVENTATO UNA MAGLIA DELLA RETE — 23 settembre 2026.
#    ⇒ `banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py`, che gira
#      da se' a ogni `--famiglia tutto` su tutte le scatole dove il prodotto
#      da' l'immagine.  Entrando nella rete ha preso tre cose che qui non
#      c'erano, e sono quelle che separano un banco di una sera da una maglia:
#        1. ⛔ il GUASTO INNESTATO (`--scena-che-lampeggia`): senza, il giorno
#           che il giudice dei pixel smettesse di guardare direbbe verde per
#           sempre e nessuno lo saprebbe;
#        2. ⛔ non sa piu' che cosa sia Plasma: la nascita e la fine della
#           sessione le legge dal REGISTRO del prodotto, e il gesto «Esci» se
#           lo cerca con la stessa domanda di `src/sessione.c`;
#        3. ⛔ l'inquilino si chiama `c20u<n>`, dentro lo spazio di nomi della
#           rete — `w4u$$` qui sotto sta FUORI, quindi il gancio non lo
#           sgombera e C19 non lo vede.
#    ⚠ Questo file RESTA: e' il documento della misura del 22 settembre, e la
#      diagnosi (i tre fotogrammi alternati, i descrittori riciclati) non sta
#      scritta da nessun'altra parte.  ⛔ Per sorvegliare il difetto si usa C20.
#
# ⛔ IL DIFETTO — 22 set 2026, la prova dell'utente su KDE con Chrome: dopo
#    «Esci» e un nuovo accesso lo schermo alternava TRE immagini (il desktop,
#    la schermata d'uscita della sessione di PRIMA, il nero).  `[M]` La
#    generazione dei buffer ripartiva da 0 con la cattura nuova, il
#    codificatore (che resta) non buttava la cache, e i descrittori riciclati
#    ritrovavano le superfici della sessione morta.
#
# ⭐ LA SCENA, ed e' il gesto dell'utente:
#    1. un inquilino nuovo si collega e resta 30 s (la sessione nasce);
#    2. «Esci»: `org.kde.Shutdown.logout` sul SUO bus (come `12-i9-logout.sh`);
#    3. si ricollega, resta 30 s, e il cliente SCRIVE il video che riceve.
#
# ⭐ DUE GIUDICI, e il primo non chiede niente al prodotto:
#    · i PIXEL: il video del secondo accesso si decodifica, e dopo i primi
#      30 fotogrammi (desktop fermo) la luminanza media dei fotogrammi deve essere UNA.
#      Se alterna fra valori lontani, e' il lampeggio.
#    · il REGISTRO: dopo la rinascita il codificatore deve dire «butto le N
#      superfici importate» per questo inquilino.
#
# ESITI: 0 verde · 1 rosso, con la ragione · 3 non ho potuto guardare
# ⛔ Un 3 non e' un verde.
# ===========================================================================
set -u
PORTA=${1:-8512}
CHI=w4u$$
PAROLA=w4-$$-parola
REG=/var/lib/rete11/registro.log
CLIENTE=/opt/remotix/01-b3-cliente.py
DOVE=$(mktemp -d /tmp/w4.XXXXXX)
trap 'loginctl terminate-user $CHI 2>/dev/null; pkill -KILL -u $CHI 2>/dev/null; sleep 1; userdel -r $CHI >/dev/null 2>&1; rm -rf "$DOVE"' EXIT

non_so() { echo "⚠ NON HO POTUTO GUARDARE (esito 3): $*"; exit 3; }

echo "== 13-w4 — la rinascita dopo «Esci» non porta fantasmi · inquilino $CHI · porta $PORTA"
useradd -m -s /bin/bash "$CHI" && printf '%s:%s\n' "$CHI" "$PAROLA" | chpasswd || non_so "useradd"
usermod -aG "$(stat -c %G /dev/dri/renderD128)" "$CHI" 2>/dev/null
usermod -aG video "$CHI" 2>/dev/null
[ -f "$REG" ] || non_so "manca $REG"

# --- 1. il primo accesso: e RESTA collegato durante «Esci» -------------------
# ⛔ `[M]` 22 set 2026: il figlio si accorge dell'uscita quando qualcuno GUARDA.
#    Il gesto dell'utente era proprio questo — «Esci» mentre guardava.
python3 "$CLIENTE" --indirizzo 127.0.0.1 --porta "$PORTA" --utente "$CHI" --parola "$PAROLA" \
	--resta 90 >"$DOVE/uno.txt" 2>&1 &
PRIMO=$!
for _ in $(seq 1 40); do pgrep -u "$CHI" -x plasmashell >/dev/null && break; sleep 1; done
pgrep -u "$CHI" -x plasmashell >/dev/null || non_so "40 s dopo il primo accesso Plasma di $CHI non c'e': la sessione non e' nata"
sleep 10
echo "   ⭐ primo accesso: la sessione Plasma di $CHI e' nata, e il cliente guarda"

# --- 2. «Esci» ---------------------------------------------------------------
SEGNO=$(wc -l <"$REG")
U=$(id -u "$CHI")
runuser -u "$CHI" -- env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$U/bus \
	busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout >/dev/null 2>&1 \
	|| non_so "org.kde.Shutdown.logout non ha risposto"
for _ in $(seq 1 30); do pgrep -u "$CHI" -x kwin_wayland >/dev/null || break; sleep 1; done
pgrep -u "$CHI" -x kwin_wayland >/dev/null && non_so "30 s dopo «Esci» KWin di $CHI e' ancora vivo"
echo "   ⭐ «Esci»: KWin di $CHI e' andato"
# ⛔ Si aspetta che il FIGLIO l'abbia visto, non solo che KWin sia morto.
#    `[M]` 22 set 2026, primo giro: ricollegato subito, il cliente e' arrivato
#    prima che il figlio dichiarasse l'uscita, ed e' stato congedato con 0x10
#    (esito 3 del banco, non del prodotto).
for _ in $(seq 1 30); do
	tail -n +"$SEGNO" "$REG" | grep -aq "sessione grafica di «$CHI» E' FINITA" && break
	sleep 1
done
tail -n +"$SEGNO" "$REG" | grep -aq "sessione grafica di «$CHI» E' FINITA" \
	|| non_so "30 s dopo «Esci» il figlio non ha dichiarato la sessione finita"
echo "   ⭐ il figlio ha visto l'uscita"
wait "$PRIMO" 2>/dev/null
sleep 2
SEGNO=$(wc -l <"$REG")

# --- 3. il nuovo accesso, col video scritto -----------------------------------
python3 "$CLIENTE" --indirizzo 127.0.0.1 --porta "$PORTA" --utente "$CHI" --parola "$PAROLA" \
	--resta 30 --video-scrivi "$DOVE/video.h264" >"$DOVE/due.txt" 2>&1
[ -s "$DOVE/video.h264" ] || non_so "il secondo accesso non ha scritto video ($(tail -1 "$DOVE/due.txt"))"
tail -n +"$SEGNO" "$REG" | grep -a "\[$CHI\]" >"$DOVE/reg.txt"
grep -aq "RIAVVIO LA CATTURA" "$DOVE/reg.txt" || non_so "nel registro nessuna rinascita della cattura dopo «Esci»"
echo "   ⭐ secondo accesso: la sessione e' rinata, $(stat -c %s "$DOVE/video.h264") byte di video"

# --- i giudici ---------------------------------------------------------------
ffmpeg -v error -i "$DOVE/video.h264" -vf "scale=64:24,format=gray" -f rawvideo "$DOVE/luma.raw" \
	|| non_so "ffmpeg non decodifica il video del secondo accesso"
PIXEL=$(python3 - "$DOVE/luma.raw" <<'P'
import sys
d=open(sys.argv[1],'rb').read(); n=64*24
m=[sum(d[i*n:(i+1)*n])//n for i in range(len(d)//n)]
# ⚠ A desktop fermo KWin consegna POCO (`[M]` 22 set 2026: 104 fotogrammi in
#   30 s): si guarda tutto quel che viene dopo i primi 30, cioe' dopo che la
#   sessione nuova si e' disegnata.
if len(m) < 50: print("3 solo %d fotogrammi decodificati" % len(m)); sys.exit()
coda=m[30:]
# a scena ferma la luminanza e' UNA: si contano i salti oltre 8 livelli
salti=sum(1 for a,b in zip(coda,coda[1:]) if abs(a-b)>8)
print("%d %d fotogrammi, coda di %d: %d salti di luminanza, valori %s" % (1 if salti>3 else 0, len(m), len(coda), salti, sorted(set(coda))[:8]))
P
)
if grep -aq "butto le [0-9]* superfici importate" "$DOVE/reg.txt"; then
	REGISTRO="0 il codificatore ha buttato le superfici della sessione di prima"
else
	REGISTRO="1 dopo la rinascita il codificatore NON ha buttato la cache"
fi
echo "   pixel:    ${PIXEL#* }"
echo "   registro: ${REGISTRO#* }"
case "${PIXEL%% *}${REGISTRO%% *}" in
	00) echo "⭐ VERDE (esito 0)"; exit 0 ;;
	3*) non_so "${PIXEL#* }" ;;
	*)  echo "⛔ ROSSO (esito 1)"; exit 1 ;;
esac
