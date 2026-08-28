#!/bin/sh
# 09-riavvia-7920.sh — IL BANCO DELLA PORTA 7920, e serve a UNA cosa che i due
#                      gemelli di stamattina non possono fare: **far morire il
#                      server apposta**.
#
# ⛔⭐ PERCHE' ESISTE, e non e' un terzo doppione.
#
#    `09-riavvia-7910.sh` accende il **dopo** del mattino accanto al **prima**
#    (7900).  Quei due restano accesi e NON si toccano: sono il termine di
#    paragone di tutte le misure gia' scritte in `fasi/09` §3-bis.
#
#    Questo ne accende un TERZO, e con due differenze che sono il suo mestiere:
#
#      1. ⛔⭐ **L'ALBERO SI SCEGLIE DA FUORI** (`ALBERO=`).  La prova della cura
#         della memoria non e' «il curato regge»: e' **due binari appaiati** —
#         il malato che DEVE morire e il curato che DEVE reggere allo stesso
#         stimolo.  Un solo binario che sopravvive non ha dimostrato niente:
#         avrebbe la stessa faccia di uno stimolo che non stimola.
#
#      2. ⛔⭐⭐ **`MALLOC_MMAP_THRESHOLD_` NELL'AMBIENTE** — ed e' la riga che
#         rende la prova possibile.  `fasi/09-il-crollo.md` §4.3-4.4: sotto i
#         128 KiB glibc serve dal mucchio e l'uso-dopo-liberazione **non fa
#         rumore**; sopra, `free()` fa `munmap` e la pagina sparisce.  E la
#         soglia e' **dinamica**: dopo il primo blocco grosso liberato si alza
#         e il difetto torna muto — ⇒ il 23 agosto il server e' morto UNA volta
#         su 45 005 fotogrammi.
#         ⭐ Impostarla **dall'ambiente** spegne l'adattamento
#         (`mp_.no_dyn_threshold = 1`): da quel momento OGNI blocco sopra la
#         soglia e' `mmap`/`munmap`, e il difetto smette di essere silenzioso
#         **per sempre**, non solo la prima volta.
#         ⚠ E' un attrezzo da BANCO, non una scelta del prodotto: e' lenta.
#
# ⭐ E `MALLOC_PERTURB_` riempie di `0x92…` la memoria liberata, cosi' anche i
#    casi piccoli — quelli che restano nel mucchio — smettono di sembrare dati
#    buoni.  ⚠ Non serve a far morire: serve a non farsi ingannare se NON muore.
#
# ⛔ E I DUE NON SI MISURANO INSIEME (`LEZIONI.md` §1.26): uno per volta.  Qui
#    la 7900 e la 7910 restano ACCESE ma FERME — un server acceso non e' un
#    banco che gira, e `09-b71-risveglio.py pulizia` le dichiara per nome
#    (`PORTE_AMMESSE`).  ⚠ Un palco orfano rimasto vivo ha gia' prodotto oggi
#    numeri plausibili e sbagliati.
#
#   sh 09-riavvia-7920.sh [opzioni in piu' per il server]
#
#   ALBERO=/media/REMOTIX/src/09c-mal-src  sh banchi/09-riavvia-7920.sh
#   ALBERO=/media/REMOTIX/src/09c-src      sh banchi/09-riavvia-7920.sh --sgombra-soglia-ms 100
#   MALLOC=no                              sh banchi/09-riavvia-7920.sh   # trappola SPENTA
#
#      porta       7920
#      lavoro      /media/REMOTIX/tmp/09c
#      albero      $ALBERO/src           (def. /media/REMOTIX/src/09c-src)
#      unita'      remotix-7920.service
#
# ⚠ Tutto il resto — le quattro trappole dell'avvio, le verifiche — e' quello
#   di `09-riavvia-7910.sh` riga per riga, e li' sta il commento per esteso.
set -e
LAV=/media/REMOTIX/tmp/09c
ALBERO=${ALBERO:-/media/REMOTIX/src/09c-src}
SRC="$ALBERO/src"
# ⛔⭐ LA PAGINA SI SCEGLIE DA FUORI — serve alla cura 4 (il riordino
#    dell'audio), che vive TUTTA in `pagina.html` e non tocca un byte del
#    binario.  ⇒ il «prima» e il «dopo» sono due FILE, serviti dallo stesso
#    identico server: cosi' l'unica variabile e' la pagina.
#    ⚠ `main.c` la legge da disco all'avvio (`pagina.c:627`), quindi basta
#      questo e un riavvio.
PAGINA=${PAGINA:-$ALBERO/src/pagina.html}
B2=/media/REMOTIX/src/b2
UNITA=remotix-7920
PORTA=7920

mkdir -p "$LAV"

LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

MANCA=$(ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
if [ "$MANCA" != "0" ]; then
  echo "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da $B2 —"
  ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3'
  exit 1
fi

# ⛔⭐ QUALE ALBERO E' — e si dichiara DAL SORGENTE, non dal nome della cartella.
#     Un nome di cartella e' un'intenzione; l'`md5` e' un fatto.
echo "albero:        $ALBERO"
echo "md5 sorgente:  $(md5sum "$SRC/webtransport.c" | cut -d' ' -f1)  webtransport.c"
echo "md5 binario:   $(md5sum "$SRC/remotix" | cut -d' ' -f1)"
echo "pagina:        $PAGINA"
echo "md5 pagina:    $(md5sum "$PAGINA" | cut -d' ' -f1)"

# ── ⛔ IL CORE: `core_pattern` di serie vale `core`, cioe' un nome RELATIVO
#    scritto nella cartella di lavoro del servizio (`/`), dove non c'e'.
#    `fasi/09-il-crollo.md` §6 punto 1: il 23 agosto il core NON c'era, e la
#    diagnosi si e' salvata solo grazie a `dmesg`.  ⇒ percorso ASSOLUTO.
VECCHIO_PATTERN=$(cat /proc/sys/kernel/core_pattern)
echo "$VECCHIO_PATTERN" > "$LAV/core_pattern.prima"
echo "$LAV/core.%e.%p.%t" > /proc/sys/kernel/core_pattern
echo "core_pattern:  $(cat /proc/sys/kernel/core_pattern)   (prima era «$VECCHIO_PATTERN», in $LAV/core_pattern.prima)"

systemctl stop "$UNITA.service" 2>/dev/null || true
systemctl reset-failed "$UNITA.service" 2>/dev/null || true
if [ -f "$LAV/pid" ]; then
  VECCHIO=$(cat "$LAV/pid")
  if kill -0 "$VECCHIO" 2>/dev/null; then
    kill "$VECCHIO"
    i=0
    while kill -0 "$VECCHIO" 2>/dev/null && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.1; done
    kill -0 "$VECCHIO" 2>/dev/null && { kill -9 "$VECCHIO"; sleep 1; }
  fi
fi
i=0
while ss -uln 2>/dev/null | grep -q ":$PORTA " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

# ── ⭐ LA TRAPPOLA DI GLIBC, e si DICHIARA se e' armata o no ────────────────
if [ "${MALLOC:-si}" = "no" ]; then
  TRAPPOLA=""
  echo "trappola glibc: ⚠ SPENTA (MALLOC=no) — l'uso-dopo-liberazione torna silenzioso"
else
  TRAPPOLA="--setenv=MALLOC_MMAP_THRESHOLD_=32768 --setenv=MALLOC_PERTURB_=165"
  echo "trappola glibc: ⭐ ARMATA — MALLOC_MMAP_THRESHOLD_=32768, MALLOC_PERTURB_=165"
fi

# ── ⭐ si parte come UNITA' DI SISTEMA, fuori da ogni sessione utente (A6) ──
# shellcheck disable=SC2086
systemd-run \
  --unit="$UNITA" --collect --description="REMOTIX, banco della porta $PORTA — fase 9, la cura della memoria" \
  --working-directory="$SRC" \
  --setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  $TRAPPOLA \
  --property=StandardOutput=append:"$LAV/registro.log" \
  --property=StandardError=append:"$LAV/registro.log" \
  --property=KillMode=mixed \
  --property=LimitRTPRIO=20 \
  --property=LimitNICE=-11 \
  --property=LimitCORE=infinity \
  "$SRC/remotix" \
  --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta $PORTA \
  --certificati "$LAV/certificati" \
  --pagina "$PAGINA" \
  --ban-file "$LAV/ban" \
  --comando-socket "$LAV/comando.sock" \
  --rilievo "$LAV/rilievo" \
  --parlantina "$@" >/dev/null

i=0
NUOVO=""
while [ $i -lt 50 ]; do
  NUOVO=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
  [ -n "$NUOVO" ] && [ "$NUOVO" != "0" ] && break
  i=$((i+1)); sleep 0.1
done
if [ -z "$NUOVO" ] || [ "$NUOVO" = "0" ]; then
  echo "⛔ il server non e' partito — le ultime righe del registro:"
  tail -15 "$LAV/registro.log"
  exit 1
fi
echo "$NUOVO" > "$LAV/pid"
echo "server $NUOVO, unita' $UNITA.service"

# ⛔⭐ E CHE LA TRAPPOLA SIA IN VIGORE SI LEGGE DAL PROCESSO VIVO, non da quel
#    che si e' scritto sopra: `LEZIONI.md` E1 — «scritto non e' in vigore».
#
# ⛔ E SI ASPETTA, esattamente come per le librerie qui sotto — e per la stessa
#    ragione, pagata subito: `[M]` 23 agosto 2026, 11:46.  `systemd-run` scrive
#    il `MainPID` quando ha FORCATO il figlio, non quando il figlio ha fatto
#    `execve`: in quella finestra `/proc/PID/environ` e' ancora l'ambiente di
#    systemd, senza nessun `MALLOC_`.  ⇒ Il primo giro ha detto «la trappola
#    NON e' nell'ambiente» mentre c'era, ed era il controllo a sbagliare.
if [ "${MALLOC:-si}" != "no" ]; then
  i=0
  while [ $i -lt 50 ]; do
    tr '\0' '\n' < "/proc/$NUOVO/environ" 2>/dev/null | grep -q '^MALLOC_MMAP_THRESHOLD_=32768$' && break
    i=$((i+1)); sleep 0.1
  done
  if tr '\0' '\n' < "/proc/$NUOVO/environ" | grep -q '^MALLOC_MMAP_THRESHOLD_=32768$'; then
    echo "⭐ VERIFICATO nell'ambiente del processo VIVO: $(tr '\0' '\n' < /proc/$NUOVO/environ | grep MALLOC | tr '\n' ' ')"
  else
    echo "⛔ la trappola NON e' nell'ambiente del processo vivo: la prova non varrebbe"
    exit 1
  fi
fi

echo "librerie che il processo VIVO ha davvero aperto:"
i=0
LIBS=""
while [ $i -lt 50 ]; do
  LIBS=$(grep -oE '/[^ ]*(libngtcp2|libnghttp3)[^ ]*' "/proc/$NUOVO/maps" 2>/dev/null | sort -u)
  if echo "$LIBS" | grep -q libngtcp2 && echo "$LIBS" | grep -q libnghttp3; then
    break
  fi
  i=$((i+1)); sleep 0.1
done
echo "$LIBS" | sed 's/^/    /'
if ! echo "$LIBS" | grep -q libngtcp2 || ! echo "$LIBS" | grep -q libnghttp3; then
  echo "⛔ NON le vedo mappate dopo 5 s: il processo non e' quello che credo"
  exit 1
fi
if echo "$LIBS" | grep -qv "$B2"; then
  echo "⛔ NON sono quelle di $B2"
  exit 1
fi

CG=$(cat "/proc/$NUOVO/cgroup" 2>/dev/null || echo "")
case "$CG" in
  *user@*|*session-*)
    echo "⛔⛔ IL SERVER STA DENTRO UNA SESSIONE UTENTE (A6 di SESSIONE.md): $CG"
    exit 1
    ;;
  *)
    echo "⭐ VERIFICATO: il server e' fuori da ogni sessione utente ($CG)"
    ;;
esac
