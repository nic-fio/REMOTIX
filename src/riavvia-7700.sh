#!/bin/sh
# Riavvia il server di prova sulla porta 7700 con la pagina che c'e' adesso su
# disco.  ⛔ La pagina si legge UNA VOLTA all'avvio (pagina.c:627): senza questo
# riavvio, una pagina nuova sul disco non arriva a nessuno.
#
#   bash riavvia-7700.sh [opzioni in piu' per il server]
#
# ⭐ Le opzioni in piu' finiscono in coda a quelle fisse, ed e' quel che rende
#    provabili i tetti lunghi di §5.3 SENZA aspettarli:
#
#      bash riavvia-7700.sh --inattivita-s 10
#
#    esercita l'orologio dei trenta minuti in dieci secondi.  ⛔ E il valore IN
#    VIGORE il server lo scrive all'avvio, cosi' non si prova un tetto credendo
#    di provarne un altro — ed e' anche l'unico modo di verificare il numero
#    predefinito senza tenere occupata una macchina per mezz'ora.
#
# ---------------------------------------------------------------------------
# ⛔⛔ QUESTO FILE VIVEVA SOLO SULLA MACCHINA DI PROVA, e non e' un dettaglio.
#
# `[M]` 16 agosto 2026: lo script che AVVIA il prodotto non era nel deposito.
# ⇒ Le sue trappole erano scritte solo dentro se stesso, nessuna revisione le
# ha mai viste, e la quarta — quella qui sotto — e' costata un'ora buona di
# diagnosi su un difetto che `SESSIONE.md` aveva gia' scritto al punto **A6**.
# ⚠ Un attrezzo fuori dal deposito e' un attrezzo che nessuno rilegge.
#
# ---------------------------------------------------------------------------
# ⛔⛔ QUATTRO TRAPPOLE, tutte misurate, tutte con lo stesso sintomo per chi
#      prova — «non mi collego» / «il desktop non parte» — e la causa minuti
#      prima.
#
#   1. L'AMBIENTE.  Il binario NON ha RPATH: senza `LD_LIBRARY_PATH` prende la
#      `ngtcp2` di sistema, parte benissimo, serve la pagina benissimo, e poi
#      ABORTA al primo che si collega con «ngtcp2_settingslen_version:
#      Unreachable».  ⇒ Si mette l'ambiente e SI VERIFICA PRIMA di fermare
#      quello che c'e': meglio niente riavvio che nessun server.
#
#   2. IL TERMINALE.  `sudo` con `use_pty` stronca tutto cio' che resta nel suo
#      pseudo-terminale quando il comando finisce, e `nohup` NON basta perche'
#      para il SIGHUP e non questo.
#
#   3. LA VERIFICA CHE NON VERIFICA.  `ldd.txt` nella cartella di lavoro NON
#      viene riscritto a ogni avvio: leggerlo dopo il riavvio da' la risposta
#      della volta scorsa.  ⇒ Le librerie si leggono da `/proc/PID/maps`, cioe'
#      da quel che il processo VIVO ha davvero aperto.
#
#   4. ⛔⭐⭐ LA SESSIONE DI CHI LO LANCIA — «A6» di `SESSIONE.md`, e la cura
#      della trappola 2 la NASCONDEVA.
#
#      `setsid` stacca dal **terminale**; ⛔ NON stacca dalla **sessione di
#      logind**.  Il processo resta nel cgroup della sessione di chi ha dato il
#      comando — tipicamente una sessione ssh — e da li' `pam_systemd`, quando
#      il figlio apre la sua sessione PAM, **vede che chi chiama sta gia' in
#      una sessione, non ne crea una seconda e non lo dice**.
#
#      `[M]` 16 agosto 2026, dopo un riavvio dato via ssh: `loginctl` non
#      mostrava NESSUNA sessione per `prova`, `/run/user/1001` non esisteva, e
#      il registro ripeteva *«NON ho il bus di sessione: Could not connect: No
#      such file or directory»* — cioe' otto giri di banco falliti su otto, e
#      la faccia del difetto era «il desktop non parte».
#
#      ⭐ La cura e' far partire il server DOVE STAREBBE IN PRODUZIONE: un'unita'
#         di sistema.  `systemd-run` ne fa una transitoria, in `system.slice`,
#         fuori da ogni sessione utente.  ⚠ E si VERIFICA dopo (E1: «scritto non
#         e' in vigore»): il cgroup del processo vivo non deve contenere
#         `user@` ne' `session-`.
set -e
LAV=/media/REMOTIX/tmp/04-vero
SRC=/media/REMOTIX/src/04-vero-src/src
B2=/media/REMOTIX/src/b2
UNITA=remotix-7700

LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

MANCA=$(ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
if [ "$MANCA" != "0" ]; then
  echo "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da $B2 —"
  ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3'
  exit 1
fi

# ── si ferma quel che c'e', in tutt'e due i modi in cui puo' essere partito ──
systemctl stop "$UNITA.service" 2>/dev/null || true
systemctl reset-failed "$UNITA.service" 2>/dev/null || true
if [ -f "$LAV/pid" ]; then
  VECCHIO=$(cat "$LAV/pid")
  if kill -0 "$VECCHIO" 2>/dev/null; then
    echo "fermo il server $VECCHIO (avvio vecchio stile)"
    kill "$VECCHIO"
    i=0
    while kill -0 "$VECCHIO" 2>/dev/null && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.1; done
    kill -0 "$VECCHIO" 2>/dev/null && { echo "non si ferma: lo forzo"; kill -9 "$VECCHIO"; sleep 1; }
  fi
fi
# ⚠ E si aspetta che la porta si liberi davvero: `[M]` 16 agosto, un avvio
#   subito dopo si e' preso «⛔ non mi lego a 0.0.0.0:7700 in UDP: Address
#   already in use» e il server nuovo e' morto senza che nessuno guardasse.
i=0
while ss -uln 2>/dev/null | grep -q ':7700 ' && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

# ── ⭐ si parte come UNITA' DI SISTEMA, fuori da ogni sessione utente ────────
systemd-run \
  --unit="$UNITA" --collect --description="REMOTIX_V2, banco della porta 7700" \
  --working-directory="$SRC" \
  --setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  --property=StandardOutput=append:"$LAV/registro.log" \
  --property=StandardError=append:"$LAV/registro.log" \
  --property=KillMode=mixed \
  --property=LimitRTPRIO=20 \
  --property=LimitNICE=-11 \
  "$SRC/remotix" \
  --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7700 \
  --certificati "$LAV/certificati" \
  --pagina "$SRC/pagina.html" \
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

# ── ⭐ LE VERIFICHE, e sono due fatti diversi ────────────────────────────────
#
# ⛔⭐ E SI ASPETTA CHE LA LISTA CI SIA, invece di leggerla e basta.
#
# `[M]` 16 agosto 2026: questo controllo ha stampato una lista **vuota** e
# subito sotto «⭐ sono quelle di /media/REMOTIX/src/b2» — cioe' ha dato l'OK
# senza aver guardato niente.  ⇒ Fra `systemd-run` che torna il `MainPID` e il
# caricatore dinamico che ha finito di mappare passano dei millisecondi, e in
# quella finestra `/proc/PID/maps` non ha ancora le librerie.
# ⚠ E' la forma piu' cattiva del difetto: non una prova rossa a torto, ma una
#   prova VERDE che non ha esaminato niente — «vuoto» e «giusto» con la stessa
#   faccia, `LEZIONI.md` §1.9.
echo "librerie che il processo VIVO ha davvero aperto:"
i=0
LIBS=""
while [ $i -lt 50 ]; do
  LIBS=$(grep -oE '/[^ ]*(libngtcp2|libnghttp3)[^ ]*' "/proc/$NUOVO/maps" 2>/dev/null | sort -u)
  # ⛔ Tutt'e DUE: una sola vorrebbe dire che il caricatore e' a meta'.
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
echo "⭐ sono quelle di $B2: si puo' provare"

# ⛔ A6: il server non dev'essere dentro NESSUNA sessione utente, o i suoi figli
#    nasceranno senza runtime, senza bus e senza desktop.
CG=$(cat "/proc/$NUOVO/cgroup" 2>/dev/null || echo "")
case "$CG" in
  *user@*|*session-*)
    echo "⛔⛔ IL SERVER STA DENTRO UNA SESSIONE UTENTE (A6 di SESSIONE.md):"
    echo "    $CG"
    echo "    ⇒ pam_systemd non creera' la sessione dei figli, e il desktop non partira'."
    exit 1
    ;;
  *)
    echo "⭐ VERIFICATO: il server e' fuori da ogni sessione utente ($CG)"
    ;;
esac
