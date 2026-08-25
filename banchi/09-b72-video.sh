#!/bin/sh
# 09-b72-video.sh — ⭐ UN VIDEO VERO A SCHERMO INTERO dentro la sessione.
#
# ⛔ ESISTE PERCHE' LE BANDE NON SONO UN VIDEO.  `04-b30-scena --movimento
#    pieno` muove tutta la superficie, ma dipinge **tinte piatte**: un
#    codificatore le comprime quasi a nulla, e misurare li' il costo di «un
#    video a schermo intero» darebbe un numero basso e **falso**.
#
# ⛔⛔ E IL LETTORE NON C'ERA — misurato il 23 agosto 2026, 08:00:
#    sulla macchina di prova **non esistono** mpv, ffplay, gst-launch-1.0,
#    totem, vlc ne' ffmpeg (ffmpeg vive solo DENTRO il contenitore, che non
#    vede il socket Wayland della sessione).  ⇒ l'unico lettore installato e'
#    ⭐ **firefox-esr**, che e' anche il lettore vero dell'utente.
#    ⚠ Quindi il numero che ne esce e' «il video **come lo riproduce
#      Firefox**», non «il video in astratto»: si dichiara, perche' un lettore
#      diverso darebbe un ritmo diverso.
#
# ⭐ IL FILMATO E' `scena-utente.webm`, cioe' **il desktop vero dell'utente**:
#    2560x1080, VP8, 17,5 s, 404 fotogrammi a ~23/s, differenza media fra
#    fotogrammi 7,66/255.  ⛔ E' **lo stesso file** su cui la fase 8 ha
#    misurato 24 956 byte per chiave (mediana, n=404): i due numeri stanno
#    sulla stessa scala e si possono confrontare.
#    ⚠ `FILM=/tmp/film-grana.webm` mette lo stesso filmato **con la grana**
#      (`noise=alls=30`), che e' il gradino verso il caso duro di `08-D2`.
#
# ⛔ Gira DA ROOT e scende all'uid dell'utente (`setpriv`), come
#    `09-b68-scena.sh`: solo lui puo' parlare col suo compositore.
#
#   UID_B=1002 UTENTE=prova2 sh 09-b72-video.sh accendi
#   sh 09-b72-video.sh -- spegni
set -u
UID_B=${UID_B:-1001}
UTENTE=${UTENTE:-prova}
FILM=${FILM:-/media/REMOTIX/src/08-D/scena-utente.webm}
LAV=${LAV:-/media/REMOTIX/tmp/09}
LOG=$LAV/b72-video.log
COPIA=/tmp/b72-film.webm
PAGINA=/tmp/b72-video.html
PROFILO=/tmp/b72-ff

if [ "${2:-}" = "spegni" ] || [ "${1:-}" = "spegni" ]; then
	pkill -u "$UID_B" -f 'firefox' 2>/dev/null
	sleep 1
	pkill -9 -u "$UID_B" -f 'firefox' 2>/dev/null
	exit 0
fi

if [ ! -f "$FILM" ]; then
	echo "VIDEO NON PARTITO: il filmato «$FILM» non c'e'"
	exit 1
fi
if ! command -v firefox-esr >/dev/null 2>&1; then
	echo "VIDEO NON PARTITO: firefox-esr non c'e', e nessun altro lettore neppure"
	exit 2
fi

# ⛔ L'utente di prova non legge dentro /media/REMOTIX: la copia serve, e coi
#    permessi giusti, o il lettore muore dicendo «non trovato».
cp -f "$FILM" "$COPIA" && chmod 644 "$COPIA"

# ⭐ La pagina: il video riempie TUTTA la superficie (`object-fit: fill`), su
#    fondo nero, in ciclo e muto.  ⛔ `muted` non e' un dettaglio: Firefox
#    blocca l'avvio automatico col suono, e il video resterebbe **fermo al
#    primo fotogramma** — cioe' la misura direbbe «un video costa quanto una
#    scena ferma», che e' un numero plausibile e falso.
cat > "$PAGINA" <<'FINE'
<!doctype html><meta charset="utf-8"><title>b72</title>
<style>html,body{margin:0;padding:0;background:#000;overflow:hidden}
video{width:100vw;height:100vh;object-fit:fill;display:block}</style>
<video id="v" src="file:///tmp/b72-film.webm" autoplay loop muted playsinline></video>
<script>
/* ⛔ `--kiosk` NON basta: misurato il 23 ago alle 08:05, la finestra copriva
   ~78 % della larghezza e la barra in alto di GNOME si vedeva ancora — cioe'
   il «video a schermo intero» non era a schermo intero, e il numero sarebbe
   stato quello di una finestra.  ⇒ si chiede lo schermo intero dal codice, e
   lo si puo' fare solo perche' il profilo mette
   `full-screen-api.allow-trusted-requests-only=false`. */
/* ⛔⛔ E LO SCHERMO INTERO SI RICHIEDE **DI CONTINUO**, non una volta.
   `ESC` e' il tasto che fa uscire dalla vista d'insieme di GNOME — ed e'
   anche il tasto che fa uscire dallo schermo intero del browser.  `[M]` 23
   ago 08:13: il punto «video» ha dato **0,202 Mbit/s**, cioe' lo stesso di
   «ferma», perche' l'ESC che serviva al compositore aveva spento lo schermo
   intero del video.  ⚠ Un numero plausibile e falso, di nuovo. */
function pieno() { try { document.documentElement.requestFullscreen(); } catch (e) {} }
addEventListener("load", pieno);
setInterval(function () {
  if (!document.fullscreenElement) pieno();
  var v = document.getElementById("v");
  if (v.paused) v.play();
}, 1000);
</script>
FINE
chmod 644 "$PAGINA"

pkill -u "$UID_B" -f 'firefox' 2>/dev/null
sleep 0.5
rm -rf "$PROFILO"
mkdir -p "$PROFILO"
# ⛔ Le preferenze non sono comodita': ognuna toglie una ragione per cui il
#    video **non** sarebbe andato, e senza la misura direbbe «un video costa
#    quanto una scena ferma».
cat > "$PROFILO/user.js" <<'FINE'
user_pref("full-screen-api.allow-trusted-requests-only", false);
user_pref("full-screen-api.warning.timeout", 0);
user_pref("full-screen-api.transition-duration.enter", "0 0");
user_pref("full-screen-api.transition-duration.leave", "0 0");
user_pref("media.autoplay.default", 0);
user_pref("media.autoplay.blocking_policy", 0);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.aboutwelcome.enabled", false);
FINE
chown -R "$UID_B:$UID_B" "$PROFILO"
: > "$LOG"
chmod 666 "$LOG"

setsid nohup setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
	env -i HOME="/home/$UTENTE" USER="$UTENTE" LANG=C.UTF-8 \
	PATH=/usr/local/bin:/usr/bin:/bin \
	XDG_RUNTIME_DIR="/run/user/$UID_B" WAYLAND_DISPLAY=wayland-0 \
	MOZ_ENABLE_WAYLAND=1 GDK_BACKEND=wayland \
	firefox-esr --profile "$PROFILO" --kiosk "file://$PAGINA" \
	>>"$LOG" 2>&1 &

# ⛔ Firefox ci mette qualche secondo: non si dichiara acceso perche' il
#    processo esiste — si aspetta che ci sia davvero.
i=0
while [ $i -lt 30 ]; do
	if pgrep -u "$UID_B" -f firefox >/dev/null; then
		sleep 6
		if pgrep -u "$UID_B" -f firefox >/dev/null; then
			echo "VIDEO ACCESO con «firefox-esr» — $COPIA"
			exit 0
		fi
		break
	fi
	i=$((i + 1))
	sleep 0.5
done
echo "VIDEO NON PARTITO — il suo registro:"
tail -30 "$LOG"
exit 1
