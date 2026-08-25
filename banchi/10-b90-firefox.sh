#!/bin/sh
# ===========================================================================
# 10-b90-firefox — ⭐ IL LETTORE DI FASE 9, PREPARATO E BASTA.
#
# ⛔⛔ PERCHE' ESISTE, ED E' UNA RAGIONE DI MISURA, NON DI COMODITA'.
#
#     Fase 9 §14.2 ha misurato le sue cinque scene mostrandole con
#     **firefox-esr**, in una pagina che stira il video su TUTTA la tela
#     (`object-fit: fill`) e che si rimette a schermo intero ogni secondo.  La
#     fase 10 mostra le sue con **mpv --fullscreen**, che tiene le proporzioni.
#     ⇒ Sullo stesso file sono DUE IMMAGINI DIVERSE, e confrontare i due
#       numeri senza dirlo e' confrontare due scene.
#     ⚠ E' meta' della domanda a cui l'incarico 10-b7 deve rispondere: **da
#       dove viene il 44,6**.  Senza il lettore di allora non si risponde.
#
# ⛔ E ALLORA PERCHE' NON `09-b72-video.sh`, CHE FA GIA' TUTTO QUESTO?
#
#     Perche' quel copione LANCIA anche, e lo fa con `setpriv … env -i
#     WAYLAND_DISPLAY=wayland-0`, cioe' **inventando l'ambiente**.  ⚠ E' la
#     forma che `09-b82-mostra.sh` e' nato per curare (fase 9, tre volte in due
#     giorni: «l'applicazione parte e resta viva, ma il desktop catturato non
#     cambia»).  ⛔ E in fase 10 c'e' un aggravante suo: `09-b72-video.sh
#     -- spegni` ammazza `firefox` **per uid**, e chi sbaglia uid spegne il
#     lettore di un ALTRO agente senza che nessuna riga lo dica.
#
# ⇒ Qui si PREPARA soltanto — profilo, preferenze, pagina — e si stampa la
#   riga di comando.  A lanciarla e' `09-b82-mostra.sh`, che legge l'ambiente
#   vero dal gestore d'utente e **conta i fotogrammi** invece di dichiarare.
#
#   sh 10-b90-firefox.sh <utente> <film> [<cartella>]
#       ⇒ stampa sull'ultima riga: PRONTO <profilo> <pagina>
# ===========================================================================
set -u
UTENTE=${1:-}
FILM=${2:-}
BASE=${3:-/tmp/10b90-ff}
[ -n "$UTENTE" ] && [ -n "$FILM" ] || { echo "⛔ uso: $0 <utente> <film>"; exit 2; }
[ "$(id -u)" -eq 0 ] || { echo "⛔ va eseguito DA ROOT"; exit 2; }
UID_U=$(id -u "$UTENTE" 2>/dev/null) || { echo "⛔ l'utente «$UTENTE» non c'e'"; exit 2; }
[ -f "$FILM" ] || { echo "⛔ il filmato «$FILM» non c'e'"; exit 2; }

D=$BASE-$UTENTE
PROFILO=$D/profilo
PAGINA=$D/pagina.html
COPIA=$D/film

rm -rf "$D"
mkdir -p "$PROFILO"

# ⛔ L'utente di prova non legge dentro /media/REMOTIX: la copia serve, coi
#    permessi giusti, o il lettore muore dicendo «non trovato» — e allora la
#    misura direbbe «un video costa quanto una scena ferma».
#    ⭐ Un collegamento duro invece di una copia: `rumore.mp4` pesa 1,2 GB e
#      copiarlo a ogni braccio sarebbe un minuto di disco per niente.
ln -f "$FILM" "$COPIA" 2>/dev/null || cp -f "$FILM" "$COPIA" || exit 2
chmod 644 "$COPIA"

# ⭐ LA PAGINA — ed e' quella di fase 9, riga per riga: il video riempie TUTTA
#    la superficie (`object-fit: fill`), fondo nero, in ciclo e muto.
#    ⛔ `muted` non e' un dettaglio: Firefox blocca l'avvio automatico col
#       suono, e il video resterebbe fermo al primo fotogramma.
cat > "$PAGINA" <<FINE
<!doctype html><meta charset="utf-8"><title>10-b90</title>
<style>html,body{margin:0;padding:0;background:#000;overflow:hidden}
video{width:100vw;height:100vh;object-fit:fill;display:block}</style>
<video id="v" src="file://$COPIA" autoplay loop muted playsinline></video>
<script>
/* ⛔⛔ LO SCHERMO INTERO SI RICHIEDE DI CONTINUO, non una volta.  \`ESC\` e' il
   tasto che fa uscire dalla vista d'insieme di GNOME ed e' anche quello che
   fa uscire dallo schermo intero del browser.  \`[M]\` fase 9, 23 ago 08:13:
   il punto «video» diede **0,202 Mbit/s**, cioe' lo stesso di «ferma», perche'
   l'ESC che serviva al compositore aveva spento lo schermo intero del video.
   ⚠ Un numero plausibile e falso. */
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

# ⛔ Le preferenze non sono comodita': ognuna toglie una ragione per cui il
#    video **non** sarebbe andato.  Sono quelle di `09-b72-video.sh`, e non una
#    di piu': aggiungerne cambierebbe il lettore che si sta ricostruendo.
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
chown -R "$UID_U:$UID_U" "$D"
chmod 755 "$D"

command -v firefox-esr >/dev/null 2>&1 || { echo "⛔ firefox-esr non c'e'"; exit 2; }
echo "PRONTO $PROFILO $PAGINA"
