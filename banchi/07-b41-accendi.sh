#!/usr/bin/env bash
#
# 07-b41 — accende UN SERVER SUO sulla macchina di prova, con il tono di prova.
#
# ⛔ PORTA, BAN-FILE, SOCKET E ALBERO PROPRI, e non e' pignoleria: il ban di
#    §4.4-bis e' per INDIRIZZO e dura 12 ore, quindi un banco che lo fa scattare
#    mette fuori uso tutti gli altri — partono tutti dallo stesso indirizzo.
#    ⚠ La 7448 e la 7700 non si toccano: sono di chi sta gia' lavorando.
#
# ⛔⛔ E L'UNITA' CONCEDE LA PRIORITA' DI TEMPO REALE — `LimitRTPRIO=20`.
#
#      E' **R26 di v1** (`~/Documenti/REMOTIX/REFERENCE.md`), misurata il 5
#      agosto 2026 e ritrovata il 17: un processo con `RLIMIT_RTPRIO` a zero —
#      il valore predefinito — **non puo' chiedere `SCHED_FIFO`**.  PipeWire ci
#      prova, gli viene negato, e il suo `data-loop` resta a priorita' normale:
#      li' dentro gira la raccolta dei campioni, che vuole un quanto di pochi
#      millisecondi ⛔ **mentre nello stesso processo il codificatore video si
#      prende un core per decine**.
#
# ⚠ Il sintomo NON e' un errore: e' «audio che scoppietta quando il desktop
#   lavora», e a desktop fermo non si riproduce.  ⇒ E' invisibile a qualunque
#   controllo sul filo, ed e' il motivo per cui tre banchi verdi non lo hanno
#   visto: misuravano i byte, non il tempo in cui arrivano.
#
# ⛔ Venti e' modesto ed e' il numero di v1: sotto i thread audio del kernel,
#    sopra qualunque cosa faccia il codificatore.
#
# ⛔ E parte come UNITA' DI SISTEMA, non da questa ssh: `setsid` stacca dal
#    terminale ma NON dalla sessione di logind, e da dentro una sessione ssh
#    `pam_systemd` non ne crea una seconda per il figlio — `/run/user/<uid>` non
#    esiste e il sintomo e' «il desktop non parte».  E' la trappola 4 di
#    `riavvia-7700.sh`, misurata il 16 agosto 2026.
#
# Uso:  bash banchi/07-b41-accendi.sh [--hz 440] [--porta 7710] [--spegni]
set -euo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA=${PAROLA:-nicfio}
HZ=440
PORTA=7710
SPEGNI=0
while [ $# -gt 0 ]; do
	case "$1" in
	--hz) HZ=$2; shift 2 ;;
	--porta) PORTA=$2; shift 2 ;;
	--spegni) SPEGNI=1; shift ;;
	*) echo "⛔ argomento ignoto: $1" >&2; exit 2 ;;
	esac
done

QUI=$(cd "$(dirname "$0")/.." && pwd)
ALBERO=/media/REMOTIX/src/07-audio-src
LAV=/media/REMOTIX/tmp/07-audio
UNITA=remotix-$PORTA

if [ "$SPEGNI" = 1 ]; then
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA' | sudo -S -p '' systemctl stop $UNITA.service 2>/dev/null; \
		 printf '%s\n' '$PAROLA' | sudo -S -p '' systemctl reset-failed $UNITA.service 2>/dev/null; \
		 echo spento"
	exit 0
fi

echo "⏳ 1/3 · porto i sorgenti in $ALBERO"
# ⛔ SENZA `sudo`, e la ragione e' costata un giro: `printf … | sudo -S` mangia
#    lo stdin, che qui E' lo stream del `tar`.  Il sintomo era «gzip: stdin: not
#    in gzip format», cioe' il `tar` che leggeva la parola d'ordine.
#    ⚠ E non serve: `/media/REMOTIX/src` e' di `nicfio` (`drwxrwxr-x`).
# ⛔ E si porta ANCHE `banchi/rcp`: il Makefile si rifiuta di compilare se non
#    puo' confrontare le due copie di `rcp.c` (R12.3).  ⚠ Passare
#    `GEMELLO=nessuno` avrebbe compilato lo stesso — e avrebbe tolto proprio il
#    controllo che stamattina ha gia' trovato un disallineamento vero.
# ⛔ E si ESCLUDONO gli oggetti e il binario del portatile.  `[M]` questo giro:
#    spedendoli, `make` sulla macchina di prova ha trovato tutto aggiornato e
#    non ha compilato NIENTE — restava il binario del portatile, legato alla
#    ngtcp2 di `/usr/local` DENTRO l'immagine.  ⭐ Il controllo `ldd` del passo 3
#    l'ha rifiutato, che e' esattamente il suo mestiere; ⚠ ma senza quel
#    controllo avrei misurato il codice del portatile credendolo del server —
#    il difetto D5, «un binario stantio resta verde».
tar -C "$QUI" --exclude='*.o' --exclude='src/remotix' -czf - src banchi/rcp | \
	ssh -o BatchMode=yes "$MACCHINA" \
	"mkdir -p $ALBERO && tar -C $ALBERO -xzf -"

echo "⏳ 2/3 · compilo dentro il contenitore"
# ⛔ Si chiama `costruisci.sh`, non `make`: e' lui che sa dove stanno ngtcp2 e
#    nghttp3 (in `/srv/src/b2`, non in `/usr`), ⭐ e fa due cose che un `make`
#    nudo non fa — cancella il binario PRIMA, cosi' «c'e'» vuol dire «e' di
#    adesso», e controlla la MARCA dentro il binario prodotto.
# ⛔ E se la compilazione fallisce ci si FERMA: senza `set -o pipefail` attorno
#    al `tail`, un `make` rosso passava inosservato e il passo 3 accendeva il
#    BINARIO VECCHIO — cioe' avrei misurato il codice di prima credendo di
#    misurare quello nuovo.  E' la forma d'errore di `01-b0-terreno.sh`.
if ! ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
	 'PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
	  bash /srv/src/07-audio-src/src/costruisci.sh 2>&1 | tail -25'"; then
	echo "⛔ la compilazione e' fallita: NON accendo niente" >&2
	exit 1
fi

echo "⏳ 3/3 · accendo il server sulla $PORTA, tono $HZ Hz"
# shellcheck disable=SC2087
# ⛔ IL COPIONE SI SPEDISCE COME FILE, non su `stdin`.
#    Stessa trappola del passo 1, e la seconda volta e' peggio della prima:
#    `printf … | sudo -S -p '' bash -s` da' a `bash` lo stdin del `printf`, che
#    dopo la parola d'ordine e' VUOTO.  ⇒ Il copione non veniva eseguito, e il
#    passo 3 stampava soltanto la sua intestazione: nessun errore, nessun
#    server.  ⚠ «Non ha fatto niente» aveva la stessa faccia di «ha funzionato».
COPIONE=$(mktemp)
trap 'rm -f "$COPIONE"' EXIT
cat > "$COPIONE" <<FINE
set -e
B2=/media/REMOTIX/src/b2
SRC=$ALBERO/src
export LD_LIBRARY_PATH="\$B2/ngtcp2/build/lib:\$B2/prefisso/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"

# ⛔ La trappola 1 di \`riavvia-7700.sh\`: senza questo controllo il binario
#    prende la ngtcp2 di sistema, parte benissimo e ABORTA al primo che si
#    collega.  Si verifica PRIMA di fermare quel che c'e'.
MANCA=\$(ldd "\$SRC/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "\$B2" || true)
if [ "\$MANCA" != "0" ]; then
	echo "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da \$B2 —"
	ldd "\$SRC/remotix" | grep -E 'ngtcp2|nghttp3'
	exit 1
fi

systemctl stop $UNITA.service 2>/dev/null || true
systemctl reset-failed $UNITA.service 2>/dev/null || true
i=0
while ss -uln 2>/dev/null | grep -q ':$PORTA ' && [ \$i -lt 50 ]; do i=\$((i+1)); sleep 0.2; done

mkdir -p $LAV
: > $LAV/registro.log

systemd-run \
	--unit=$UNITA --collect --description="REMOTIX_V2, banco 07-b41 (audio)" \
	--working-directory="\$SRC" \
	--setenv=LD_LIBRARY_PATH="\$LD_LIBRARY_PATH" \
	--property=StandardOutput=append:$LAV/registro.log \
	--property=StandardError=append:$LAV/registro.log \
	--property=KillMode=mixed \
	--property=LimitRTPRIO=20 \
	--property=LimitNICE=-11 \
	"\$SRC/remotix" \
	--indirizzo 0.0.0.0 --nome 192.168.0.2 --porta $PORTA \
	--certificati $LAV/certificati \
	--pagina "\$SRC/pagina.html" \
	--ban-file $LAV/ban \
	--comando-socket $LAV/comando.sock \
	--rilievo $LAV/rilievo \
	--audio-prova $HZ \
	--parlantina >/dev/null

i=0; PID=0
while [ \$i -lt 50 ]; do
	PID=\$(systemctl show -p MainPID --value $UNITA.service 2>/dev/null || echo 0)
	[ "\$PID" != "0" ] && [ -n "\$PID" ] && break
	i=\$((i+1)); sleep 0.1
done
if [ "\$PID" = "0" ] || [ -z "\$PID" ]; then
	echo "⛔ il server non e' partito — le ultime righe:"
	tail -20 $LAV/registro.log
	exit 1
fi
echo "⭐ server \$PID sulla porta $PORTA, unita' $UNITA.service"
sleep 1
grep -E "TONO DI PROVA|in ascolto|impronta" $LAV/registro.log | head -6 || true
FINE

scp -q -o BatchMode=yes "$COPIONE" "$MACCHINA:/tmp/07-b41-accendi-remoto.sh"
ssh -o BatchMode=yes "$MACCHINA" \
	"printf '%s\n' '$PAROLA' | sudo -S -p '' bash /tmp/07-b41-accendi-remoto.sh"
